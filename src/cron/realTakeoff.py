"""
Most of the take-offs shown on the map have time and location delayed by the
data filtering. This cronjob is to look up the true take-off location and ts
by following the path back in time.
"""

from datetime import datetime
from typing import List
import tzlocal
import pytz

from airfieldManager import AirfieldManager
from configuration import dbConnectionInfo, INFLUX_DB_HOST, INFLUX_DB_NAME
from dataStructures import LogbookItem, addressPrefixes
from db.DbSource import DbSource
from db.InfluxDbThread import InfluxDbThread
from utils import getGroundSpeedThreshold


class RealTakeoffLookup(object):
    RUN_INTERVAL = 60  # [s]

    def __init__(self):
        print(f"[INFO] RealTakeoffLookup scheduled to run every {self.RUN_INTERVAL}s.")

        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST, startThread=False)
        self.airfieldManager = AirfieldManager()

    def __del__(self):
        self.influxDb.client.close()

    def _listTakeoffs(self, ts) -> List[LogbookItem]:
        strSql = f"SELECT id, ts, address, address_type, location_icao FROM logbook_events " \
                 f"WHERE ts >= {ts - self.RUN_INTERVAL} AND event='T';"

        l = []
        with DbSource(dbConnectionInfo).getConnection().cursor() as c:
            c.execute(strSql)

            # while row := c.fetchone():
            while True:
                row = c.fetchone()
                if not row:
                    break

                id, ts, address, address_type, location_icao = row
                item = LogbookItem(id=id, takeoff_ts=ts, address=address, address_type=address_type, takeoff_icao=location_icao)
                l.append(item)

        return l

    def checkTakeoffs(self):
        ts = int(datetime.now().timestamp())  # [s]
        takeoffs = self._listTakeoffs(ts)

        modifiedTakeoffs = 0
        for logbookItem in takeoffs:
            addr = f"{addressPrefixes[logbookItem.address_type]}{logbookItem.address}"
            windowEndTs = logbookItem.takeoff_ts - 2    # [s]
            windowStartTs = windowEndTs - 59            # [s]

            q = f"select * from pos where addr='{addr}' " \
                f"and time >= {windowStartTs}000000000 and time <= {windowEndTs}000000000 " \
                f"order by time desc"
            rs = self.influxDb.query(q)

            if rs:
                rows = [row for row in rs.get_points()]

                dirty = False
                minGs = 666e+666
                minGsIndex = 0
                for i, row in enumerate(rows):
                    groundSpeed = row['gs']
                    if groundSpeed < minGs:
                        minGsIndex = i
                        minGs = groundSpeed
                        if groundSpeed <= 80:    # getGroundSpeedThreshold(logbookItem.aircraft_type, forEvent='T'):
                            break

                if minGsIndex > 0:
                    logbookItem.takeoff_ts = row['time']  # ts in string format!!
                    logbookItem.takeoff_lat = row['lat']
                    logbookItem.takeoff_lon = row['lon']
                    dirty = True

                if dirty:
                    if not logbookItem.takeoff_icao:
                        logbookItem.takeoff_icao = self.airfieldManager.getNearest(logbookItem.takeoff_lat, logbookItem.takeoff_lon)

                    # the DB stores datetime as Europe-local (UTC+2/1) - shift from influx's UTC to local:
                    utcDt = datetime.strptime(logbookItem.takeoff_ts, '%Y-%m-%dT%H:%M:%S%z')
                    localTz = tzlocal.get_localzone()
                    localDt = utcDt.astimezone(localTz)
                    logbookItem.takeoff_ts = int(localDt.timestamp())

                    locationIcao = f"'{logbookItem.takeoff_icao}'" if logbookItem.takeoff_icao else 'null'

                    updateSql = f"UPDATE logbook_events SET ts={logbookItem.takeoff_ts}, " \
                                f"lat={logbookItem.takeoff_lat}, lon={logbookItem.takeoff_lon}, " \
                                f"location_icao={locationIcao} " \
                                f"WHERE id={logbookItem.id};"

                    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
                        cur.execute(updateSql)

                    modifiedTakeoffs += 1

        print(f"[INFO] Num take-off amendments: {modifiedTakeoffs}/{len(takeoffs)}")


if __name__ == '__main__':
    l = RealTakeoffLookup()
    l.checkTakeoffs()
