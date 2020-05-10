import time
from datetime import datetime
from threading import Thread

from redis import StrictRedis
from queue import Queue, Empty

from ogn.parser import parse
from ogn.parser.exceptions import ParseError

from configuration import SPEED_THRESHOLD, redisConfig, dbConnectionInfo, REDIS_RECORD_EXPIRATION, NUM_RAW_WORKERS
from db.DbThread import DbThread
from airfieldManager import AirfieldManager


class RawWorker(Thread):

    redis = StrictRedis(**redisConfig)

    def __init__(self, index: int, dbThread: DbThread, rawQueue: Queue):
        super(RawWorker, self).__init__()

        self.index = index
        self.dbThread = dbThread
        self.rawQueue = rawQueue

        self.doRun = True

    def __del__(self):
        self.doRun = False

    def stop(self):
        self.doRun = False

    def run(self):
        print(f"[INFO] Starting worker #{self.index}")
        while self.doRun:
            try:
                raw_message = self.rawQueue.get(block=False)
                if raw_message:
                    self._processMessage(raw_message)
            except Empty:
                time.sleep(1)   # ~ thread.yield()

        print(f"[INFO] Worker #{self.index} terminated.")

    def _processMessage(self, raw_message: str):
        beacon = None
        try:
            beacon = parse(raw_message)
            if not beacon or 'beacon_type' not in beacon.keys() or beacon['beacon_type'] != 'aprs_aircraft':
                return

        except ParseError as e:
            # print('[ERROR] when parsing a beacon: {}'.format(e.message))
            # print("Failed BEACON:", raw_message)
            return

        except Exception as e:
            # print('[ERROR] {}'.format(e))
            # if beacon:
            #     print("Failed BEACON:", beacon)
            return

        # we are not interested in para, baloons, uavs, static stuff and others:
        if beacon['aircraft_type'] in [4, 6, 7, 13, 11, 15, 16]:
            return

        address = beacon['address']
        groundSpeed = beacon['ground_speed']
        # print(f"[INFO] {address} gs: {groundSpeed:.0f}")

        currentStatus = 0 if groundSpeed < SPEED_THRESHOLD else 1    # 0 = on ground, 1 = airborne, -1 = unknown
        # TODO add AGL check (?)

        statusKey = f"{address}-status"
        prevStatus = self.redis.get(statusKey)

        if not prevStatus:  # we have no prior information
            self.redis.set(statusKey, currentStatus)
            self.redis.expire(statusKey, REDIS_RECORD_EXPIRATION)
            return

        if currentStatus != int(prevStatus):
            self.redis.set(statusKey, currentStatus)
            self.redis.expire(statusKey, REDIS_RECORD_EXPIRATION)

            ts = round(beacon['timestamp'].timestamp())     # [s]
            addressType = beacon['address_type']
            aircraftType = beacon['aircraft_type']
            lat = beacon['latitude']
            lon = beacon['longitude']

            icaoLocation = AirfieldManager().getNearest(lat, lon)
            if not icaoLocation:
                return

            event = 'L' if currentStatus == 0 else 'T'  # L = landing, T = take-off

            dt = datetime.fromtimestamp(ts)
            dtStr = dt.strftime('%H:%M:%S')
            print(f"[INFO] {dtStr} {icaoLocation} {address} {event}")

            strSql = f"INSERT INTO logbook_events " \
                f"(ts, address, address_type, aircraft_type, event, lat, lon, location_icao) " \
                f"VALUES " \
                f"({ts}, '{address}', {addressType}, '{aircraftType}', " \
                f"'{event}', {lat:.5f}, {lon:.5f}, '{icaoLocation}');"

            # print('strSql:', strSql)

            self.dbThread.addStatement(strSql)


class BeaconProcessor(object):

    redis = StrictRedis(**redisConfig)

    rawQueue = Queue()
    workers = list()

    def __init__(self):

        # restore unprocessed data from redis:
        numRead = 0
        while True:
            item = self.redis.lpop('rawQueue')
            if not item:
                break
            self.rawQueue.put(item)
            numRead += 1
        print(f"[INFO] Loaded {numRead} raw messages from redis.")

        self.dbThread = DbThread(dbConnectionInfo)
        self.dbThread.start()

        for i in range(NUM_RAW_WORKERS):
            rawWorker = RawWorker(index=i, dbThread=self.dbThread, rawQueue=self.rawQueue)
            rawWorker.start()
            self.workers.append(rawWorker)

    def stop(self):
        for worker in self.workers:
            worker.stop()

        # store all unprocessed data into redis:
        print('[INFO] Flushing rawQueue into redis..', end='')
        for item in list(self.rawQueue.queue):
            self.redis.rpush('rawQueue', item)
        print('done.')

        self.dbThread.stop()

        print('[INFO] BeaconProcessor terminated.')

    startTime = time.time()
    numEnquedTasks = 0

    def enqueueForProcessing(self, raw_message: str):
        self.rawQueue.put(raw_message)

        self.numEnquedTasks += 1

        now = time.time()
        tDiff = now - self.startTime
        if tDiff >= 60:
            numTasksPerMin = self.numEnquedTasks/tDiff*60
            numQueuedTasks = self.rawQueue.qsize()

            print(f"Beacon rate: {numTasksPerMin:.0f}/min. {numQueuedTasks} queued.")

            self.numEnquedTasks = 0
            self.startTime = now

