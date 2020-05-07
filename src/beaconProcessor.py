import re
import time
import datetime

from redis import StrictRedis
from rq import Queue

from configuration import SPEED_THRESHOLD, redisConfig, dbConnectionInfo, REDIS_RECORD_EXPIRATION
from db.DbThread import DbThread
from db.DbSource import DbSource
from airfieldManager import AirfieldManager


class BeaconProcessor(object):

    redis = StrictRedis(**redisConfig)
    queue = Queue('beacons', is_async=False, connection=redis)

    def __init__(self):
        # self.dbThread = DbThread(dbConnectionInfo)
        # self.dbThread.start()
        pass

    # def __del__(self):
    #     self.dbThread.stop()

    def _processBeacon(self, beacon: dict):
        if beacon['beacon_type'] != 'aprs_aircraft':
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

            print(f"[INFO] {address} {event} {icaoLocation}")

            strSql = f"INSERT INTO logbook_events " \
                     f"(ts, address, address_type, aircraft_type, event, lat, lon, location_icao) " \
                     f"VALUES " \
                     f"(%s, %s, %s, %s, %s, %s, %s, %s);"

            data = (ts, address, addressType, aircraftType, event, float(f"{lat:.5f}"), float(f"{lon:.5f}"), icaoLocation)

            with DbSource(dbConnectionInfo).getConnection() as cur:
                # query = cur.mogrify(strSql, data)
                # print('query:', query)
                # self.dbThread.addStatement(query)
                cur.execute(strSql, data)

    startTime = time.time()
    numEnquedTasks = 0

    def enqueueForProcessing(self, beacon: dict):
        self.queue.enqueue(self._processBeacon, beacon)
        self.numEnquedTasks += 1

        now = time.time()
        tDiff = now - self.startTime
        if tDiff >= 60:
            numTasksPerMin = self.numEnquedTasks/tDiff*60
            numQueuedTasks = len(self.queue)

            if numQueuedTasks > 666:
                print('Throughput: {:.0f}/min. We are {:.1f} min behind.'.format(numTasksPerMin, numQueuedTasks / numTasksPerMin))
            else:
                print('Throughput: {:.0f}/min'.format(numTasksPerMin))

            self.numEnquedTasks = 0
            self.startTime = now


