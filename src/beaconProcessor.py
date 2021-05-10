"""
Notes:
    * multiple workers cannot work on a single queue as flight-states need to be processed in order.
    * hence multiple queues exist to paralelise processing a bit using queue-specific workers
"""
import os
import time
import sys
import pytz
from datetime import datetime
from threading import Thread

from redis import StrictRedis
from queue import Queue, Empty

from ogn.parser import parse
from ogn.parser.exceptions import ParseError

from configuration import DEBUG, redisConfig, \
    dbConnectionInfo, REDIS_RECORD_EXPIRATION, MQ_HOST, MQ_PORT, MQ_USER, MQ_PASSWORD, INFLUX_DB_NAME, INFLUX_DB_HOST, \
    GEOFILE_PATH, AGL_LANDING_LIMIT, ADDRESS_TYPES, ADDRESS_TYPE_PREFIX
from geofile import Geofile
from db.DbThread import DbThread
from db.InfluxDbThread import InfluxDbThread
from airfieldManager import AirfieldManager
from dataStructures import Status
from utils import getGroundSpeedThreshold
from periodicTimer import PeriodicTimer


class RawWorker(Thread):

    def __init__(self, id: int, dbThread: DbThread, rawQueue: Queue, influxDb: InfluxDbThread):
        super(RawWorker, self).__init__()

        self.id = id
        self.dbThread = dbThread
        self.rawQueue = rawQueue
        self.influxDb = influxDb

        self.numProcessed = 0
        self.airfieldManager = AirfieldManager()
        self.geofile = Geofile(filename=GEOFILE_PATH)
        self.redis = StrictRedis(**redisConfig)

        self.doRun = True

    def __del__(self):
        self.doRun = False

    def stop(self):
        self.doRun = False

    def run(self):
        print(f"[INFO] Starting worker '{self.id}'")
        while self.doRun:
            try:
                raw_message = self.rawQueue.get(block=False)
                if raw_message:
                    self._processMessage(raw_message)
            except Empty:
                time.sleep(1)   # ~ thread.yield()
            except BrokenPipeError as ex:
                print('[WARN] in worker:', str(ex))
            except Exception as ex:
                print('[ERROR] some other problem:', str(ex))

        print(f"[INFO] Worker '{self.id}' terminated.")

    def _saveToRedis(self, key: str, value, expire=REDIS_RECORD_EXPIRATION):
        self.redis.set(key, str(value))
        self.redis.expire(key, expire)

    def _getFromRedis(self, key, default=None):
        res = self.redis.get(key)
        if not res:
            return default
        else:
            return res.decode('utf-8')

    def _getAgl(self, lat, lon,  altitude):
        """
        :param lat:
        :param lon:
        :param altitude:
        :return:
        """
        elev = self.geofile.getValue(lat, lon)
        if elev and 100000 >= elev > -100:  # 100 km is the edge of space ;)
            if elev:
                agl = altitude - elev

                if agl < 0:
                    agl = 0

                return agl

        return None

    def _processMessage(self, raw_message: str):
        beacon = None
        try:
            beacon = parse(raw_message)
            if not beacon or 'aprs_type' not in beacon.keys() or (beacon.get('aprs_type', None) != 'position'):
                # print('[WARN] cannot process:', raw_message)
                # print('bt:', beacon.get('beacon_type', None), str(beacon))
                return

        except ParseError as e:
            # print(f'[ERROR] when parsing a beacon: {str(e)}', raw_message, file=sys.stderr)
            return

        except Exception as e:
            # print(f'[ERROR] Some other error in _processMessage() {str(e)}', raw_message, file=sys.stderr)
            return

        self.numProcessed += 1

        addressType = beacon.get('address_type', 1)     # 1 = icao, 2 = flarm, 3 = ogn
        addressTypeStr = ADDRESS_TYPES.get(addressType, 'X')
        aircraftType = beacon.get('aircraft_type', 8)   # icao-crafts are often 'powered aircraft's

        if 'address' not in beacon:
            address = beacon['name'][3:]
            beacon['address_type'] = 1
        else:
            address = beacon['address']

        # we are not interested in para, baloons, uavs and other crazy flying stuff:
        if aircraftType not in [1, 2, 6, 8, 9, 10]:
            return

        dt = beacon['timestamp'].replace(tzinfo=pytz.UTC)
        ts = round(dt.timestamp())  # [s]
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        if ts - now.timestamp() > 30:    # timestamp from the future? We'll 30s time offset at most..
            print(f"[WARN] Timestamp from the future: {dt}, now is {now}")
            return

        lat = beacon.get('latitude') or None            # [deg]
        lon = beacon.get('longitude') or None           # [deg]
        altitude = int(beacon.get('altitude')) or 0     # [m]
        groundSpeed = beacon.get('ground_speed') or 0   # [km/h]
        verticalSpeed = beacon.get('climb_rate') or 0   # [m/s]
        turnRate = beacon.get('turn_rate') or 0         # [deg/s]

        if addressType == 1 and groundSpeed > 400:  # ignore fast (icao) airliners and jets
            return

        # get altitude above ground level (AGL):
        agl = self._getAgl(lat, lon, altitude)  # [m]

        # insert into influx:
        # pos ~ position, vs = vertical speed, tr = turn rate
        if agl is None or agl < 128000:    # groundSpeed > 0 and
            aglStr = 0 if agl is None else f"{agl:.0f}"
            q = f"pos,addr={ADDRESS_TYPE_PREFIX[addressType]}{address} lat={lat:.6f},lon={lon:.6f},alt={altitude:.0f},gs={groundSpeed:.2f},vs={verticalSpeed:.2f},tr={turnRate:.2f},agl={aglStr} {ts}000000000"
            self.influxDb.addStatement(q)

        prevStatus: Status = None
        statusKey = f"{addressTypeStr}{address}-status"
        ps = self._getFromRedis(statusKey)
        if ps:
            try:
                prevStatus = Status.parse(ps)
            except ValueError as e:
                print('[ERROR] when parsing prev. status: ', e)

        gsKey = f"{addressTypeStr}{address}-gs"

        if not prevStatus:  # we have no prior information
            self._saveToRedis(statusKey, Status(s=0, ts=ts))    # 0 = on ground, 1 = airborne, -1 = unknown
            self._saveToRedis(gsKey, 0, 120)    # gs = 0
            return

        prevGroundSpeed = float(self._getFromRedis(gsKey, 0))
        if prevGroundSpeed > 0:
            # filter speed change a bit (sometimes there are glitches in speed with badly placed gps antenna):
            groundSpeed = groundSpeed * 0.7 + prevGroundSpeed * 0.3

        self._saveToRedis(gsKey, groundSpeed, 3600)

        currentStatus: Status = Status(ts=ts, s=-1)    # 0 = on ground, 1 = airborne, -1 = unknown

        if prevStatus.s == 0:   # 0 = on ground, 1 = airborne, -1 = unknown
            currentStatus.s = 1 if groundSpeed >= getGroundSpeedThreshold(aircraftType, forEvent='T') else 0
        else:   # when airborne
            currentStatus.s = 0 if groundSpeed <= getGroundSpeedThreshold(aircraftType, forEvent='L') else 1

        if currentStatus.s != prevStatus.s:
            event = 'L' if currentStatus.s == 0 else 'T'  # L = landing, T = take-off
            flightTime = 0

            if event == 'L':
                flightTime = currentStatus.ts - prevStatus.ts   # [s]
                if flightTime < 120:    # [s]
                    return

                if flightTime > 12 * 3600:  # some relic from the previous day
                    self.redis.delete(statusKey)
                    self.redis.delete(gsKey)
                    return

                # check altitude above ground level:
                if agl and agl > AGL_LANDING_LIMIT:   # [m]
                    return  # most likely a false detection

            elif event == 'T':
                # check altitude above ground level:
                if agl is not None and agl < 50:  # [m]
                    return  # most likely a false detection

            self._saveToRedis(statusKey, currentStatus)

            icaoLocation = self.airfieldManager.getNearest(lat, lon)

            dt = datetime.fromtimestamp(ts)
            dtStr = dt.strftime('%H:%M:%S')
            print(f"[INFO] event: {dtStr}; {icaoLocation}; [{addressTypeStr}] {address}; {event}; {flightTime}")

            icaoLocation = f"'{icaoLocation}'" if icaoLocation else 'null'

            strSql = f"INSERT INTO logbook_events " \
                f"(ts, address, address_type, aircraft_type, event, lat, lon, location_icao, flight_time) " \
                f"VALUES " \
                f"({ts}, '{address}', {addressType}, '{aircraftType}', " \
                f"'{event}', {lat:.5f}, {lon:.5f}, {icaoLocation}, {flightTime});"

            # print('strSql:', strSql)

            self.dbThread.addStatement(strSql)


class BeaconProcessor(object):

    redis = StrictRedis(**redisConfig)

    rawQueueOGN = Queue(maxsize=0)  # 0 ~ infinite (according to docs)
    rawQueueFLR = Queue(maxsize=0)
    rawQueueICA = Queue(maxsize=0)
    queues = (rawQueueOGN, rawQueueFLR, rawQueueFLR, rawQueueICA)   # FLR is present twice to create two worker threads for flarm processing
    queueIds = ('ogn', 'flarm1', 'flarm2', 'icao')                  # (the FLR traffic is way higher than others; but ICA is also nearing processing limits)

    workers = list()

    def __init__(self):

        # restore unprocessed data from redis:
        numRead = 0
        for key, queue in zip(self.queueIds, self.queues):
            while True:
                item = self.redis.lpop(key)
                if not item:
                    break
                queue.put(item)
                numRead += 1
        print(f"[INFO] Loaded {numRead} raw message(s) from redis.")

        self.dbThread = DbThread(dbConnectionInfo)
        self.dbThread.start()

        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)
        self.influxDb.start()

        for id, queue in zip(self.queueIds, self.queues):
            rawWorker = RawWorker(id=id, dbThread=self.dbThread, rawQueue=queue, influxDb=self.influxDb)
            rawWorker.start()
            self.workers.append(rawWorker)

        self.timer = PeriodicTimer(60, self._processStats)
        self.timer.start()

    def stop(self):
        for worker in self.workers:
            worker.stop()

        # store all unprocessed data into redis:
        n = 0
        for key, queue in zip(self.queueIds, self.queues):
            n += queue.qsize()
            for item in list(queue.queue):
                self.redis.rpush(key, item)
        print(f"[INFO] Flushed {n} rawQueueX items into redis.")

        self.dbThread.stop()
        self.influxDb.stop()

        self.timer.stop()

        print('[INFO] BeaconProcessor terminated.')

    startTime = time.time()
    numEnquedTasks = 0

    def _processStats(self):
        now = time.time()
        tDiff = now - self.startTime
        numTasksPerMin = self.numEnquedTasks/tDiff*60
        numQueuedTasks = self.rawQueueOGN.qsize() + self.rawQueueFLR.qsize() + self.rawQueueICA.qsize()
        print(f"[INFO] Beacon rate: {numTasksPerMin:.0f}/min. {numQueuedTasks} queued.")

        traffic = dict()
        for worker in self.workers:
            traffic[worker.id] = worker.numProcessed
            worker.numProcessed = 0

        if not DEBUG and numTasksPerMin >= 10:
            cmd = f"mosquitto_pub -h {MQ_HOST} -p {MQ_PORT} -u {MQ_USER} -P {MQ_PASSWORD} -t ognLogbook/rate -m '{round(numTasksPerMin)}'; " \
                  f"mosquitto_pub -h {MQ_HOST} -p {MQ_PORT} -u {MQ_USER} -P {MQ_PASSWORD} -t ognLogbook/queued -m '{round(numQueuedTasks)}'; " \
                  f"mosquitto_pub -h {MQ_HOST} -p {MQ_PORT} -u {MQ_USER} -P {MQ_PASSWORD} -t ognLogbook/ogn -m '{traffic['ogn']}'; " \
                  f"mosquitto_pub -h {MQ_HOST} -p {MQ_PORT} -u {MQ_USER} -P {MQ_PASSWORD} -t ognLogbook/flarm -m '{traffic['flarm1'] + traffic['flarm2']}'; " \
                  f"mosquitto_pub -h {MQ_HOST} -p {MQ_PORT} -u {MQ_USER} -P {MQ_PASSWORD} -t ognLogbook/icao -m '{traffic['icao']}';"
            os.system(cmd)

        self.numEnquedTasks = 0
        self.startTime = now

    def enqueueForProcessing(self, raw_message: str):
        prefix = raw_message[:3]
        if prefix == 'OGN':
            self.rawQueueOGN.put(raw_message)
        elif prefix == 'FLR':
            self.rawQueueFLR.put(raw_message)
        elif prefix == 'ICA':
            self.rawQueueICA.put(raw_message)
        else:
            print(f'[WARN] Worker for "{prefix}" not implemented!', raw_message, file=sys.stderr)
            return

        self.numEnquedTasks += 1


