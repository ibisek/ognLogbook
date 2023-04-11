"""
Notes:
    * multiple workers cannot work on a single queue as flight-states need to be processed in order.
    * hence multiple queues exist to paralelise processing a bit using queue-specific workers
"""

import logging
import os
import time
import sys
import pytz
from datetime import datetime
from threading import Thread
import multiprocessing as mp

from redis import StrictRedis
from queue import Queue, Empty

from ogn.parser import parse
from ogn.parser.exceptions import ParseError

from configuration import DEBUG, redisConfig, \
    dbConnectionInfo, REDIS_RECORD_EXPIRATION, MQ_HOST, MQ_PORT, MQ_USER, MQ_PASSWORD, INFLUX_DB_NAME, INFLUX_DB_HOST, INFLUX_DB_NAME_PERMANENT_STORAGE, \
    GEOFILE_PATH, AGL_LANDING_LIMIT, ADDRESS_TYPES, ADDRESS_TYPE_PREFIX, USE_MULTIPROCESSING_INSTEAD_OF_THREADS
from geofile import Geofile
from db.DbThread import DbThread
from db.InfluxDbThread import InfluxDbThread
from dao.ddb import DDB, DDBRecord
from dao.permanentStorage import PermanentStorageFactory
from airfieldManager import AirfieldManager
from dataStructures import Status
from utils import getGroundSpeedThreshold
from periodicTimer import PeriodicTimer
from expiringDict import ExpiringDict
from cron.eventWatcher.eventWatcher import EventWatcher


class RawWorker(Thread):

    def __init__(self, id: int, rawQueue: Queue, addrType: str, dbThread: DbThread = None, influxDb: InfluxDbThread = None):
        """
        :param id:          worker identifier
        :param rawQueue:    shared queue with work to process
        :param addrType:    O/I/F/..
        :param dbThread:    if not supplied own will be created and closed upon exit
        :param influxDb:    if not supplied own will be created and closed upon exit
        """

        super(RawWorker, self).__init__()

        self.id = id

        self.rawQueue = rawQueue

        if dbThread:
            self.dbThread = dbThread
            self.ownDbThread = False
        else:
            self.dbThread = DbThread(dbConnectionInfo)
            self.dbThread.start()
            self.ownDbThread = True

        if influxDb:
            self.influxDb = influxDb
            self.ownInfluxDb = False
        else:
            self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)
            self.influxDb.start()
            self.ownInfluxDb = True

        self.influxDb_ps = InfluxDbThread(dbName=INFLUX_DB_NAME_PERMANENT_STORAGE, host=INFLUX_DB_HOST)
        self.influxDb_ps.start()

        self.numProcessed = mp.Value('i', 0) if USE_MULTIPROCESSING_INSTEAD_OF_THREADS else 0
        self.airfieldManager = AirfieldManager()
        self.geofile = Geofile(filename=GEOFILE_PATH)
        self.redis = StrictRedis(**redisConfig)
        self.beaconDuplicateCache = ExpiringDict(ttl=1)     # [s]

        self.permanentStorage = PermanentStorageFactory.storageFor(addrType)

        self.beaconType = addrType  # O/I/F/.. keeps the info for which beacon type is processed by this worker

        self.doRun = True

    def __del__(self):
        self.doRun = False
        if self.ownDbThread:
            self.dbThread.stop()
        if self.ownInfluxDb:
            self.influxDb.stop()
        self.influxDb_ps.stop()

    def stop(self):
        self.doRun = False

    # def runProc(self, id: int, dbThread: DbThread, rawQueue: Queue, influxDb: InfluxDbThread):
    #     self.id = id
    #     self.dbThread = dbThread
    #     self.rawQueue = rawQueue
    #     self.influxDb = influxDb
    #
    #     self.run()

    def run(self):
        print(f"[INFO] Starting worker '{self.id}'")
        while self.doRun:
            try:
                raw_message = self.rawQueue.get(block=False)
                if raw_message:
                    self._processMessage(raw_message)
            except Empty:
                try:
                    time.sleep(1)  # ~ thread.yield()
                except KeyboardInterrupt:
                    self.stop()
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

    def _getAgl(self, lat, lon, altitude):
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

    def _retainAircraftRegistration(self, raw_message, address):
        """
        OGNEMO beacons contain aircraft registration which may not be in the DDB. For that matter
        this is to extract the registration
        :param raw_message:
        :param address:
        :return:
        """

        ddb = DDB.getInstance()
        ddbRec = ddb.get('I', address)
        if ddbRec:
            if not ddbRec.aircraft_registration:
                registration = raw_message[:raw_message.index('>')]     # duplicate code #1
                if not registration:
                    return

                ddbRec.aircraft_registration = registration
                ddbRec.dirty = True
        else:
            registration = raw_message[:raw_message.index('>')]     # duplicate code #2 to avoid parsing the string for performance reasons
            if not registration:
                return

            ddbRec = DDBRecord()
            ddbRec.device_type = 'I'
            ddbRec.device_id = address
            ddbRec.aircraft_registration = registration
            ddb.insert(ddbRec)

        if ddbRec.dirty:
            # Workaround: in multiprocessing environment the DDB instance is unique per process and thus cannot be synced from cronJobs!
            # Furthermore, new on-the-fly DDB records are based on the OGNEMO beacons and inserted only in the ICAO process.
            ddb.cron()

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

        if USE_MULTIPROCESSING_INSTEAD_OF_THREADS:
            self.numProcessed.value += 1
        else:
            self.numProcessed += 1

        addressType = beacon.get('address_type', 1)  # 0=sky, 1 = icao, 2 = flarm, 3 = ogn
        addressTypeStr = ADDRESS_TYPES.get(addressType, 'X')
        aircraftType = beacon.get('aircraft_type', 8)  # icao-crafts are often 'powered aircraft's (8)

        if 'address' not in beacon:
            beacon['address_type'] = 1      # 1 = icao
            if len(beacon['name']) == 9:    # with prefix; e.g. OGN123456
                address = beacon['name'][3:]
            else:
                address = beacon['comment'][4:10]   # NEMO beacon address is in comment
        else:
            address = beacon['address']

        # we are not interested in para, baloons, uavs and other crazy flying stuff:
        if aircraftType not in [1, 2, 6, 8, 9, 10]:
            return

        dt = beacon['timestamp'].replace(tzinfo=pytz.UTC)
        ts = round(dt.timestamp())  # UTC [s]
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        if ts - now.timestamp() > 30:  # timestamp from the future? We'll 30s time offset at most..
            # print(f"[WARN] Timestamp from the future: {dt}, now is {now}")
            return

        lat = beacon.get('latitude') or None  # [deg]
        lon = beacon.get('longitude') or None  # [deg]
        altitude = int(beacon.get('altitude')) or 0  # [m]
        groundSpeed = beacon.get('ground_speed') or 0  # [km/h]
        verticalSpeed = beacon.get('climb_rate') or 0  # [m/s]
        turnRate = beacon.get('turn_rate') or 0  # [deg/s]

        # skip beacons we received for the second time and got already processed:
        key = f"{addressTypeStr}{address}-{lat:.4f}{lon:.4f}{altitude}{groundSpeed:.1f}{verticalSpeed:.1f}"
        if key in self.beaconDuplicateCache:
            del self.beaconDuplicateCache[key]
            return
        else:
            self.beaconDuplicateCache[key] = True   # store a marker in the cache .. will be dropped after TTL automatically later

        if addressType == 1 and groundSpeed > 400:  # ignore fast (icao) airliners and jets
            return

        # extract beacon signal strength (if available):
        signalStrength = 0
        temp = raw_message[:raw_message.index('dB')] if 'dB' in raw_message else None
        if temp:
            signalStrength = round(float(temp[temp.rfind(' '):].strip()))

        # get altitude above ground level (AGL):
        agl = self._getAgl(lat, lon, altitude)  # [m]

        # insert into influx:
        # pos ~ position, vs = vertical speed, tr = turn rate
        if agl is None or agl < 128000:  # groundSpeed > 0 and
            aglStr = 0 if agl is None else f"{agl:.0f}"
            q = f"pos,addr={ADDRESS_TYPE_PREFIX[addressType]}{address} lat={lat:.6f},lon={lon:.6f},alt={altitude:.0f},gs={groundSpeed:.2f},vs={verticalSpeed:.2f},tr={turnRate:.2f},agl={aglStr},ss={signalStrength} {ts}000000000"

            if self.permanentStorage.eligible4ps(address):  # shall be saved into permanent storage?
                self.influxDb_ps.addStatement(q)
            else:
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
            self._saveToRedis(statusKey, Status(s=0, ts=ts))  # 0 = on ground, 1 = airborne, -1 = unknown
            self._saveToRedis(gsKey, 0, 120)  # gs = 0
            return

        prevGroundSpeed = float(self._getFromRedis(gsKey, 0))
        if prevGroundSpeed > 0:
            # filter speed change a bit (sometimes there are glitches in speed with badly placed gps antenna):
            groundSpeed = groundSpeed * 0.7 + prevGroundSpeed * 0.3

        self._saveToRedis(gsKey, groundSpeed, 3600)

        currentStatus: Status = Status(ts=ts, s=-1)  # 0 = on ground, 1 = airborne, -1 = unknown

        if prevStatus.s == 0:  # 0 = on ground, 1 = airborne, -1 = unknown
            currentStatus.s = 1 if groundSpeed >= getGroundSpeedThreshold(aircraftType, forEvent='T') else 0
        else:  # when airborne
            currentStatus.s = 0 if groundSpeed <= getGroundSpeedThreshold(aircraftType, forEvent='L') else 1

        if currentStatus.s != prevStatus.s:
            event = 'L' if currentStatus.s == 0 else 'T'  # L = landing, T = take-off
            flightTime = 0

            if event == 'L':
                flightTime = currentStatus.ts - prevStatus.ts  # [s]
                if flightTime < 120:  # [s]
                    return

                if flightTime > 12 * 3600:  # some relic from the previous day
                    self.redis.delete(statusKey)
                    self.redis.delete(gsKey)
                    return

                # check altitude above ground level:
                if agl and agl > AGL_LANDING_LIMIT:  # [m]
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
                     f"({ts}, '{address}', '{addressTypeStr}', '{aircraftType}', " \
                     f"'{event}', {lat:.5f}, {lon:.5f}, {icaoLocation}, {flightTime});"

            # print('strSql:', strSql)
            self.dbThread.addStatement(strSql)

            icaoLocation = icaoLocation.replace("'", '')
            EventWatcher.createEvent(redis=self.redis,
                                     ts=ts, event=event, address=address, addressType=addressType,
                                     lat=lat, lon=lon, icaoLocation=icaoLocation, flightTime=flightTime)

            if self.beaconType == 'I' and "OGNEMO" in raw_message[:16]:     # ICAO worker processes OGNEMO beacons that carry registration
                self._retainAircraftRegistration(address=address, raw_message=raw_message)

        self.beaconDuplicateCache.tick()    # cleanup the cache (cannot be called from PeriodicTimer due to subprocess/threading troubles :|)


class BeaconProcessor(object):
    redis = StrictRedis(**redisConfig)

    if USE_MULTIPROCESSING_INSTEAD_OF_THREADS:
        mpManager = mp.Manager()  # create a set of multiprocessing (shared) queues
        rawQueueOGN = mpManager.Queue()
        rawQueueFLR = mpManager.Queue()
        rawQueueICA = mpManager.Queue()
        rawQueueSKY = mpManager.Queue()
    else:
        rawQueueOGN = Queue()
        rawQueueFLR = Queue()
        rawQueueICA = Queue()
        rawQueueSKY = Queue()

    queues = (rawQueueOGN, rawQueueFLR, rawQueueFLR, rawQueueICA, rawQueueSKY)  # one worker's performance on current CPU is 35k/min
    queueIds = ('ogn', 'flarm1', 'flarm2', 'icao1', 'sky1')
    addrTypes = ('O', 'F', 'F', 'I', 'S')
    # TODO there shall be separate queues for each worker and traffic shall be split/shaped evenly for every worker of the same kind..

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

        for id, queue, addrType in zip(self.queueIds, self.queues, self.addrTypes):
            rawWorker = RawWorker(id=id, rawQueue=queue, addrType=addrType)
            if USE_MULTIPROCESSING_INSTEAD_OF_THREADS:
                instance = mp.Process(target=rawWorker.run)
            else:
                instance = Thread(target=rawWorker.run)
            instance.start()

            self.workers.append(rawWorker)

        self.timer = PeriodicTimer(60, self._processStats)
        self.timer.start()

    def stop(self):
        for worker in self.workers:
            worker.stop()

        # store all unprocessed data into redis:
        # n = 0
        # for key, queue in zip(self.queueIds, self.queues):
        #     n += queue.qsize()
        #     # for item in list(queue.queue):
        #     try:
        #         while item := queue.get(block=False):
        #             self.redis.rpush(key, item)
        #     except Empty:
        #         pass
        # print(f"[INFO] Flushed {n} rawQueueX items into redis.")

        self.timer.stop()

        print('[INFO] BeaconProcessor terminated.')

    startTime = time.time()
    numEnquedTasks = 0

    def _processStats(self):
        now = time.time()
        tDiff = now - self.startTime
        numTasksPerMin = self.numEnquedTasks / tDiff * 60
        numQueuedTasks = self.rawQueueOGN.qsize() + self.rawQueueFLR.qsize() + self.rawQueueICA.qsize() + self.rawQueueSKY.qsize()
        print(f"[INFO] Beacon rate: {numTasksPerMin:.0f}/min, {numQueuedTasks} queued.")

        traffic = dict()
        for worker in self.workers:
            if USE_MULTIPROCESSING_INSTEAD_OF_THREADS:
                traffic[worker.id] = worker.numProcessed.value
                worker.numProcessed.value = 0
            else:
                traffic[worker.id] = worker.numProcessed
                worker.numProcessed = 0

        if not DEBUG and numTasksPerMin >= 10:
            cmd = f"mosquitto_pub -h {MQ_HOST} -p {MQ_PORT} -u {MQ_USER} -P {MQ_PASSWORD} -t ognLogbook/rate -m '{round(numTasksPerMin)}'; " \
                  f"mosquitto_pub -h {MQ_HOST} -p {MQ_PORT} -u {MQ_USER} -P {MQ_PASSWORD} -t ognLogbook/queued -m '{round(numQueuedTasks)}'; "

            trafficKeys = ['ogn', 'flarm1', 'icao1', 'sky1']
            for trafficType in trafficKeys:
                n = traffic[trafficType]
                if n > 100:
                    t = trafficType[:-1] if trafficType.endswith('1') else trafficType
                    cmd += f"mosquitto_pub -h {MQ_HOST} -p {MQ_PORT} -u {MQ_USER} -P {MQ_PASSWORD} -t ognLogbook/{t} -m '{traffic[trafficType]}';"

            os.system(cmd)

        self.numEnquedTasks = 0
        self.startTime = now

    def enqueueforProcessingWithPrefix(self, raw_message: str, prefix: str):
        if prefix == 'OGN':
            self.rawQueueOGN.put(raw_message)
        elif prefix == 'FLR':
            self.rawQueueFLR.put(raw_message)
        elif prefix == 'ICA':
            self.rawQueueICA.put(raw_message)
        elif prefix == 'SKY':
            self.rawQueueSKY.put(raw_message)
        else:
            print(f'[WARN] Worker for "{prefix}" not implemented!', raw_message, file=sys.stderr)
            return

        self.numEnquedTasks += 1

    def enqueueForProcessing(self, raw_message: str):
        prefix = raw_message[:3]
        self.enqueueforProcessingWithPrefix(raw_message, prefix)
