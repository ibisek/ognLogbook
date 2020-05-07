import re
import datetime

from redis import StrictRedis
from rq import Queue

from configuration import SPEED_THRESHOLD, redisConfig, dbConnectionInfo
from db.DbThread import DbThread
from db.DbSource import DbSource


class BeaconParser(object):

    redis = StrictRedis(**redisConfig)
    queue = Queue('beacons', is_async=True, connection=redis)

    def __init__(self):
        # self.dbThread = DbThread(dbConnectionInfo)
        # self.dbThread.start()
        pass

    # def __del__(self):
    #     self.dbThread.stop()

    def _processBeacon(self, beacon: dict):
        if beacon['beacon_type'] != 'aprs_aircraft':
            return

        address = beacon['address']
        groundSpeed = beacon['ground_speed']
        print(f"[INFO] {address} gs: {groundSpeed:.0f}")

        currentStatus = 0 if groundSpeed < SPEED_THRESHOLD else 1    # 0 = on ground, 1 = airborne, -1 = unknown

        statusKey = f"{address}-status"
        prevStatus = self.redis.get(statusKey)

        if not prevStatus:  # we have no prior information
            self.redis.set(statusKey, currentStatus)
            return

        prevStatus = int(prevStatus)

        if currentStatus != prevStatus:
            self.redis.set(statusKey, currentStatus)

            ts = round(beacon['timestamp'].timestamp())     # [s]
            addressType = beacon['address_type']
            aircraftType = beacon['aircraft_type']
            lat = beacon['latitude']
            lon = beacon['longitude']

            event = 'L' if currentStatus == 0 else 'T'  # L = landing, T = take-off

            strSql = f"INSERT INTO logbook_events (ts, address, address_type, aircraft_type, event, lat, lon) " \
                     f"VALUES (%(ts)s, %(address)s, %(address_type)s, %(aircraft_type)s, %(event)s, %(lat)s, %(lon)s);"

            data = dict()
            data['ts'] = ts
            data['address'] = address
            data['address_type'] = addressType
            data['aircraft_type'] = aircraftType
            data['event'] = event
            data['lat'] = float(f"{lat:.5f}")
            data['lon'] = float(f"{lon:.5f}")

            with DbSource(dbConnectionInfo).getConnection() as cur:
                query = cur.mogrify(strSql, data)
                print('query:', query)
                # self.dbThread.addStatement(query)
                cur.execute(strSql, data)

    def enqueueForProcessing(self, beacon: dict):
        self.queue.enqueue(self._processBeacon, beacon)
        # print("Qlen:", len(self.queue))
        # jid = self.queue.job_ids[0]
        # job = self.queue.fetch_job(jid)
        # print(job)

