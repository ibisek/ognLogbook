import re
import time
from datetime import datetime

from redis import StrictRedis
from rq import Queue
# from queue import Queue

from ogn.parser import parse
from ogn.parser.exceptions import ParseError

from configuration import SPEED_THRESHOLD, redisConfig, dbConnectionInfo, REDIS_RECORD_EXPIRATION
from db.DbThread import DbThread
from db.DbSource import DbSource
from airfieldManager import AirfieldManager
from dataStructures import ProcessedBeacon



class BeaconProcessor(object):

    redis = StrictRedis(**redisConfig)
    rawQueue = Queue('raw', is_async=True, connection=redis)
    eventsQueue = Queue('events', is_async=True, connection=redis)

    def __init__(self):
        # self.dbThread = DbThread(dbConnectionInfo)
        # self.dbThread.start()
        pass

    # def __del__(self):
    #     self.dbThread.stop()

    def _processMessage(self, raw_message: str):
        beacon = None
        try:
            beacon = parse(raw_message)
            if 'beacon_type' not in beacon.keys() or beacon['beacon_type'] != 'aprs_aircraft':
                return

        except ParseError as e:
            print('[ERROR] {}'.format(e.message))
            if beacon:
                print("Failed BEACON:", beacon)
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

            # icaoLocation = AirfieldManager().getNearest(lat, lon)
            # if not icaoLocation:
            #     return

            event = 'L' if currentStatus == 0 else 'T'  # L = landing, T = take-off

            dt = datetime.fromtimestamp(ts)
            dtStr = dt.strftime('%H:%M:%S')
            print(f"[INFO] {dtStr} {address} {event}")

            data: ProcessedBeacon = ProcessedBeacon(
                ts=ts,
                address=address,
                addressType=addressType,
                aircraftType=aircraftType,
                event=event,
                lat=float(f"{lat:.5f}"),
                lon=float(f"{lon:.5f}"),
                location_icao=None
            )

            self.eventsQueue.enqueue(self._lookupIcaoLocation, data)

    def _lookupIcaoLocation(self, beacon: ProcessedBeacon):
        location_icao = AirfieldManager().getNearest(beacon.lat, beacon.lon)

        if location_icao:
            dt = datetime.fromtimestamp(beacon.ts)
            dtStr = dt.strftime('%H:%M:%S')

            print(f"[INFO] {dtStr} {location_icao} {beacon.address} {beacon.event}")

            strSql = f"INSERT INTO logbook_events " \
                     f"(ts, address, address_type, aircraft_type, event, lat, lon, location_icao) " \
                     f"VALUES " \
                     f"(%s, %s, %s, %s, %s, %s, %s, %s);"

            data = (beacon.ts, beacon.address, beacon.addressType, beacon.aircraftType, beacon.event,
                    beacon.lat, beacon.lon, location_icao)

            with DbSource(dbConnectionInfo).getConnection() as cur:
                cur.execute(strSql, data)

    startTime = time.time()
    numEnquedTasks = 0

    def enqueueForProcessing(self, raw_message: str):
        self.rawQueue.enqueue(self._processMessage, raw_message)
        self.numEnquedTasks += 1

        now = time.time()
        tDiff = now - self.startTime
        if tDiff >= 60:
            numTasksPerMin = self.numEnquedTasks/tDiff*60
            numQueuedTasks = len(self.rawQueue)

            if numQueuedTasks > 666:
                print(f"Beacon rate: {numTasksPerMin:.0f}/min. {numQueuedTasks} queued.")
            else:
                print('Beacon rate: {:.0f}/min'.format(numTasksPerMin))

            self.numEnquedTasks = 0
            self.startTime = now


