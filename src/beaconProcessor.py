"""
Notes:
    * multiple workers cannot work on a single queue as flight-states need to be processed in order.
    * hence multiple queues exist to paralelise processing a bit using queue-specific workers
"""
import time
from datetime import datetime
from threading import Thread

from redis import StrictRedis
from queue import Queue, Empty

from ogn.parser import parse
from ogn.parser.exceptions import ParseError

from configuration import SPEED_THRESHOLD, redisConfig, dbConnectionInfo, REDIS_RECORD_EXPIRATION
from db.DbThread import DbThread
from airfieldManager import AirfieldManager
from dataStructures import Status


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

    def _saveToRedis(self, statusKey: str, status: Status):
        self.redis.set(statusKey, str(status))
        self.redis.expire(statusKey, REDIS_RECORD_EXPIRATION)

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
        aircraftType = beacon['aircraft_type']
        if aircraftType in [4, 6, 7, 13, 11, 15, 16]:
            return

        address = beacon['address']
        groundSpeed = beacon['ground_speed']
        ts = round(beacon['timestamp'].timestamp())  # [s]
        # print(f"[INFO] {address} gs: {groundSpeed:.0f}")

        # print('[DEBUG] Gps H:', beacon['gps_quality']['horizontal'])

        currentStatus: Status = Status(ts=ts)
        currentStatus.s = 0 if groundSpeed < SPEED_THRESHOLD else 1    # 0 = on ground, 1 = airborne, -1 = unknown
        # TODO add AGL check (?)
        # TODO threshold by aircraftType

        prevStatus: Status = None
        statusKey = f"{address}-status"
        ps = self.redis.get(statusKey)
        if ps:
            try:
                prevStatus = Status.parse(ps)
            except ValueError as e:
                print('[ERROR] when parsing prev. status: ', e)

        if not prevStatus:  # we have no prior information
            self._saveToRedis(statusKey, currentStatus)
            return

        if currentStatus.s != prevStatus.s:
            addressType = beacon['address_type']
            aircraftType = beacon['aircraft_type']
            lat = beacon['latitude']
            lon = beacon['longitude']

            icaoLocation = AirfieldManager().getNearest(lat, lon)
            if not icaoLocation:
                return

            event = 'L' if currentStatus.s == 0 else 'T'  # L = landing, T = take-off
            flightTime = 0
            if event == 'L':
                flightTime = currentStatus.ts - prevStatus.ts   # [s]
                if flightTime < 60:
                    return

            self._saveToRedis(statusKey, currentStatus)

            dt = datetime.fromtimestamp(ts)
            dtStr = dt.strftime('%H:%M:%S')
            print(f"[INFO] {dtStr}; {icaoLocation}; {address}; {event}; {flightTime}")

            strSql = f"INSERT INTO logbook_events " \
                f"(ts, address, address_type, aircraft_type, event, lat, lon, location_icao, flight_time) " \
                f"VALUES " \
                f"({ts}, '{address}', {addressType}, '{aircraftType}', " \
                f"'{event}', {lat:.5f}, {lon:.5f}, '{icaoLocation}', {flightTime});"

            # print('strSql:', strSql)

            self.dbThread.addStatement(strSql)


class BeaconProcessor(object):

    redis = StrictRedis(**redisConfig)

    rawQueueOGN = Queue()
    rawQueueFLR = Queue()
    rawQueueICA = Queue()
    queues = (rawQueueOGN, rawQueueFLR, rawQueueICA)
    queueKeys = ('rawQueueOGN', 'rawQueueFLR', 'rawQueueICA')

    workers = list()

    def __init__(self):

        # restore unprocessed data from redis:
        numRead = 0
        for key, queue in zip(self.queueKeys, self.queues):
            while True:
                item = self.redis.lpop(key)
                if not item:
                    break
                queue.put(item)
                numRead += 1
        print(f"[INFO] Loaded {numRead} raw message(s) from redis.")

        self.dbThread = DbThread(dbConnectionInfo)
        self.dbThread.start()

        for i, queue in enumerate(self.queues):
            rawWorker = RawWorker(index=i, dbThread=self.dbThread, rawQueue=queue)
            rawWorker.start()
            self.workers.append(rawWorker)

    def stop(self):
        for worker in self.workers:
            worker.stop()

        # store all unprocessed data into redis:
        n = 0
        for key, queue in zip(self.queueKeys, self.queues):
            n += queue.qsize()
            for item in list(queue.queue):
                self.redis.rpush(key, item)
        print(f"[INFO] Flushed {n} rawQueueX items into redis.")

        self.dbThread.stop()

        print('[INFO] BeaconProcessor terminated.')

    startTime = time.time()
    numEnquedTasks = 0

    def _printStats(self):
        now = time.time()
        tDiff = now - self.startTime
        if tDiff >= 60:
            numTasksPerMin = self.numEnquedTasks/tDiff*60
            numQueuedTasks = self.rawQueueOGN.qsize() + self.rawQueueFLR.qsize() + self.rawQueueICA.qsize()

            print(f"Beacon rate: {numTasksPerMin:.0f}/min. {numQueuedTasks} queued.")

            self.numEnquedTasks = 0
            self.startTime = now

    def enqueueForProcessing(self, raw_message: str):
        self._printStats()

        prefix = raw_message[:3]
        if prefix == 'OGN':
            self.rawQueueOGN.put(raw_message)
        elif prefix == 'FLR':
            self.rawQueueFLR.put(raw_message)
        else:   # 'ICA'
            self.rawQueueICA.put(raw_message)

        self.numEnquedTasks += 1


