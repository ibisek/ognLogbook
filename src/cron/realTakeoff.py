"""
Most of the take-offs shown on the map have time and location delayed by the
data filtering. This cronjob is to look up the true take-off location and ts
by following the path back in time.
"""

from queue import Queue, Empty
from datetime import datetime
from typing import List

from configuration import dbConnectionInfo, INFLUX_DB_HOST, INFLUX_DB_NAME
from db.DbSource import DbSource
from db.InfluxDbThread import InfluxDbThread
from dataStructures import LogbookItem, addressPrefixes
from utils import getGroundSpeedThreshold


class RealTakeoffLookup(object):
    RUN_INTERVAL = 60  # [s]

    def __init__(self):
        self.queue = Queue()
        print(f"[INFO] RealTakeoffLookup scheduled to run every {self.RUN_INTERVAL}s.")

        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST, startThread=False)

    def __del__(self):
        self.influxDb.client.close()

    def _listTakeoffs(self, ts) -> List[LogbookItem]:
        strSql = f"SELECT id, ts, address, address_type FROM logbook_events " \
                 f"WHERE ts >= {ts - self.RUN_INTERVAL} AND event='T';"

        l = []
        with DbSource(dbConnectionInfo).getConnection().cursor() as c:
            c.execute(strSql)

            # while row := c.fetchone():
            while True:
                row = c.fetchone()
                if not row:
                    break

                id, ts, address, address_type = row
                item = LogbookItem(id=id, takeoff_ts=ts, address=address, address_type=address_type)
                l.append(item)

        return l

    def checkTakeoffs(self):
        ts = int(datetime.now().timestamp())  # [s]
        takeoffs = self._listTakeoffs(ts)

        modifiedTakeoffs = 0
        for logbookItem in takeoffs:
            addr = f"{addressPrefixes[logbookItem.address_type]}{logbookItem.address}"
            windowEndTs = logbookItem.takeoff_ts - 2    # [s]
            windowStartTs = windowEndTs - 40            # [s]

            q = f"select * from pos where addr='{addr}' " \
                f"and time >= {windowStartTs}000000000 and time <= {windowEndTs}000000000 " \
                f"order by time desc"
            rs = self.influxDb.query(q)

            if rs:
                dirty = False
                for row in rs.get_points():
                    groundSpeed = row['gs']
                    if groundSpeed >= 80:    # getGroundSpeedThreshold(logbookItem.aircraft_type, forEvent='T'):
                        logbookItem.takeoff_ts = row['time']    # ts in string format!!
                        logbookItem.takeoff_lat = row['lat']
                        logbookItem.takeoff_lon = row['lon']
                        dirty = True

                    else:
                        break

                if dirty:
                    logbookItem.takeoff_ts = int(datetime.strptime(logbookItem.takeoff_ts, '%Y-%m-%dT%H:%M:%SZ').timestamp())

                    updateSql = f"UPDATE logbook_events SET ts={logbookItem.takeoff_ts}, " \
                                f"lat={logbookItem.takeoff_lat}, lon={logbookItem.takeoff_lon} " \
                                f"WHERE id={logbookItem.id};"

                    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
                        cur.execute(updateSql)

                    modifiedTakeoffs += 1

        print(f"[INFO] Num take-off amendments: {modifiedTakeoffs}/{len(takeoffs)}")


if __name__ == '__main__':
    l = RealTakeoffLookup()
    l.checkTakeoffs()
