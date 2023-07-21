"""
(1) Find "orphaned" records in redis (with last status update >= 30 min),
(2) Check last known status of the aircraft from influx,
(3) if dAlt < 0 (descending) and alt < 100m and near to an airfield create landing event,
(4) mark as landed in redis.
"""

from datetime import datetime
from redis import StrictRedis
import tzlocal

from configuration import dbConnectionInfo, redisConfig, INFLUX_DB_NAME, INFLUX_DB_HOST, REDIS_RECORD_EXPIRATION, ADDRESS_TYPE_PREFIX, REVERSE_ADDRESS_TYPE
from db.DbThread import DbThread
from db.InfluxDbThread import InfluxDbThread
from utils import getGroundSpeedThreshold
from airfieldManager import AirfieldManager
from dao.logbookDao import findMostRecentTakeoff
from dataStructures import LogbookItem
from cron.eventWatcher.eventWatcher import EventWatcher


class RedisReaper(object):
    RUN_INTERVAL = 5*60  # [s]

    REDIS_STALE_INTERVAL = 40 * 60  # [s]   // 40 min shall be enough even for a patient pilot to find a reasonable thermal ;)
    GS_THRESHOLD = getGroundSpeedThreshold(1, 'L')

    def __init__(self):
        print(f"[INFO] RedisReaper(lite) scheduled to run every {self.RUN_INTERVAL}s.")

        self.dbt = DbThread(dbConnectionInfo=dbConnectionInfo)
        self.dbt.start()

        self.redis = StrictRedis(**redisConfig)
        self.influx = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)

        self.airfieldManager = AirfieldManager()

    def doWork(self):
        airborne = []

        keys = self.redis.keys('*status')   # TODO uz davno nemusi byt airborne!!
        for key in keys:
            key = key.decode('ascii')
            # ttl = self.redis.ttl(key)
            value = self.redis.get(key)
            if value:   # entries could have been deleted in the mean while..
                status = int(value.decode('ascii').split(';')[0])
                if status == 1:  # 1 = airborne
                    addr = key.split('-')[0]    # in fact addressTypeStr + addr (e.g. I123456, F123456, O123456, ..)
                    airborne.append(addr)

        numLanded = 0
        for addr in airborne:
            # TODO overit, jestli je stale jeste airborne!! pokud ne, tak skip!!

            prefix = addr[:1]
            addr = addr[1:]
            addrType = prefix   # REVERSE_ADDRESS_TYPE.get(prefix, None)
            addrPrefixLong = ADDRESS_TYPE_PREFIX.get(REVERSE_ADDRESS_TYPE.get(prefix, None), None)

            if not addrPrefixLong:
                continue

            try:
                # fetch last received beacon:
                rs = self.influx.client.query(f"SELECT * FROM pos WHERE addr='{addrPrefixLong}{addr}' ORDER BY time DESC LIMIT 1;")
            except Exception:
                continue

            for res in rs:
                # print('res:', res)
                time = res[0]['time']
                agl = res[0]['agl'] if res[0]['agl'] else 0
                alt = res[0]['alt'] if res[0]['alt'] else 0
                gs = res[0]['gs']
                lat = res[0]['lat']
                lon = res[0]['lon']

                try:
                    utcDt = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S%z')  # UTC
                except ValueError:
                    try:
                        utcDt = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S.%fZ')  # UTC
                    except ValueError:
                        continue

                localDt = utcDt.astimezone(tzlocal.get_localzone())
                localTs = int(localDt.timestamp())

                landingSuspected = False
                if 0 < agl < 100 and gs < self.GS_THRESHOLD:
                    landingSuspected = True
                else:
                    lastBeaconAge = datetime.now().timestamp() - localTs
                    if lastBeaconAge > self.REDIS_STALE_INTERVAL:
                        landingSuspected = True

                if landingSuspected:
                    icaoLocation = self.airfieldManager.getNearest(lat, lon)
                    # if not icaoLocation:  # no outlandings yet..
                    #     continue

                    # print(f"addr: {addr}; dt: {dt / 60:.0f}min ; agl: {agl:.0f}m near {icaoLocation}")

                    # set status as Landed in redis (or delete?):
                    key = f"{prefix}{addr}-status"
                    self.redis.set(key, '0;0')  # 0 = on-ground; ts=0 to indicate forced landing
                    self.redis.expire(key, REDIS_RECORD_EXPIRATION)

                    # look-up related takeoff data:
                    logbookItem: LogbookItem = findMostRecentTakeoff(addr, addrType)

                    if logbookItem:
                        # create a LANDING logbook_event -> a stored procedure then creates a logbook_entry:
                        flightTime = localTs - logbookItem.takeoff_ts
                        if flightTime < 0:
                            flightTime = 0

                        icaoLocationVal = f"'{icaoLocation}'" if icaoLocation else 'null'
                        strSql = f"INSERT INTO logbook_events " \
                                 f"(ts, address, address_type, aircraft_type, event, lat, lon, location_icao, flight_time) " \
                                 f"VALUES " \
                                 f"({localTs}, '{addr}', '{logbookItem.address_type}', '{logbookItem.aircraft_type}', " \
                                 f"'L', {lat:.5f}, {lon:.5f}, {icaoLocationVal}, {flightTime});"

                        # print('strSql:', strSql)

                        self.dbt.addStatement(strSql)

                        addrTypeNum = REVERSE_ADDRESS_TYPE.get(addrType, 1)
                        EventWatcher.createEvent(redis=self.redis,
                                                 ts=localTs, event='L', address=addr, addressType=addrTypeNum,
                                                 lat=lat, lon=lon, icaoLocation=icaoLocation, flightTime=flightTime)

                        numLanded += 1

        if numLanded > 0:
            print(f"[INFO] RedisReaper: cleared {numLanded} stale record(s)")

    def stop(self):
        self.dbt.stop()


if __name__ == '__main__':
    r = RedisReaper()
    r.doWork()
    r.stop()

    print('KOHEU.')
