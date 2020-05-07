import re
import datetime

from redis import StrictRedis
from rq import Queue

from configuration import SPEED_THRESHOLD, redisConfig, dbConnectionInfo
from db.DbThread import DbThread
from db.DbSource import DbSource


class BeaconParser(object):
    addressPattern = '"address":.?"(.+?)"'
    addrRegex = re.compile(addressPattern, re.IGNORECASE)
    gsPattern = '"ground_speed":.?(.+?),'
    gsRegex = re.compile(gsPattern, re.IGNORECASE)

    dtPattern = 'datetime.datetime\\((\\d{4}), (\\d{1,2}), (\\d{1,2}), (\\d{1,2}), (\\d{1,2}), (\\d{1,2})\\)'
    dtRegex = re.compile(dtPattern, re.IGNORECASE)
    atPattern = '"aircraft_type":.?(.+?),'
    atRegex = re.compile(atPattern, re.IGNORECASE)
    latPattern = '"latitude":.?(.+?),'
    latRegex = re.compile(latPattern, re.IGNORECASE)
    lonPattern = '"longitude":.?(.+?),'
    lonRegex = re.compile(lonPattern, re.IGNORECASE)

    redis = StrictRedis(**redisConfig)
    queue = Queue('beacons', is_async=False, connection=redis)

    def __init__(self):
        # self.dbThread = DbThread(dbConnectionInfo)
        # self.dbThread.start()
        pass

    # def __del__(self):
    #     self.dbThread.stop()

    def parseInitialInfo(self, line: str):
        address = None
        groundSpeed = None

        m = self.addrRegex.search(line)
        if m:
            address = m.groups()[0]
        else:
            raise ValueError(f"Cannot not parse {line}")

        m = self.gsRegex.search(line)
        if m:
            groundSpeed = float(m.groups()[0])
        else:
            raise ValueError(f"Cannot not parse {line}")

        return address, groundSpeed

    def parseExtendedInfo(self, line: str):
        m = self.dtRegex.search(line)
        if m:
            year = int(m.groups()[0])
            month = int(m.groups()[1])
            day = int(m.groups()[2])
            hour = int(m.groups()[3])
            min = int(m.groups()[4])
            sec = int(m.groups()[5])
            dt = datetime.datetime(year, month, day, hour, min, sec)
            ts = round(dt.timestamp())  # [s]

        m = self.atRegex.search(line)
        if m:
            aircraftType = int(m.groups()[0])

        m = self.latRegex.search(line)
        if m:
            lat = float(m.groups()[0])

        m = self.lonRegex.search(line)
        if m:
            lon = float(m.groups()[0])

        return ts, aircraftType, lat, lon

    def parseLine(self, line: str):
        if 'aprs_aircraft' not in line:
            return

        line = line.replace('\'', '"')

        address, groundSpeed = self.parseInitialInfo(line)
        # print("info 1:", address, groundSpeed)

        currentStatus = 0 if groundSpeed < SPEED_THRESHOLD else 1    # 0 = on ground, 1 = airborne, -1 = unknown

        statusKey = f"{address}-status"
        prevStatus = self.redis.get(statusKey)

        if not prevStatus:  # we have no prior information
            self.redis.set(statusKey, currentStatus)
            return

        prevStatus = int(prevStatus)

        if currentStatus != prevStatus:
            self.redis.set(statusKey, currentStatus)

            ts, aircraftType, lat, lon = self.parseExtendedInfo(line)
            # print("info 2:", ts, aircraftType, lat, lon)

            event = 'L' if currentStatus == 0 else 'T'  # L = landing, T = take-off

            strSql = f"INSERT INTO logbook_events (ts, address, aircraft_type, event, lat, lon, location_icao) " \
                     f"VALUES (%(ts)s, %(address)s, %(aircraft_type)s, %(event)s, %(lat)s, %(lon)s, %(icao_location)s)"
            # print('strSql:', strSql)

            data = dict()
            data['ts'] = ts
            data['address'] = address
            data['aircraft_type'] = aircraftType
            data['event'] = event
            data['lat'] = float(f"{lat:.5f}")
            data['lon'] = float(f"{lon:.5f}")
            data['icao_location'] = 'tdb'

            with DbSource(dbConnectionInfo).getConnection() as cur:
                # query = cur.mogrify(strSql, data)
                # print('query:', query)
                # self.dbThread.addStatement(query)
                cur.execute(strSql, data)

    def processBeacon(self, beacon: str):
        self.queue.enqueue(self.parseLine, beacon)
