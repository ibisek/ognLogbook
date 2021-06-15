"""
A cron service to calculate real flown distance (point-to-point) for each flight.
"""

from math import radians

from configuration import dbConnectionInfo, INFLUX_DB_HOST, INFLUX_DB_NAME
from db.DbSource import DbSource
from db.InfluxDbThread import InfluxDbThread
from airfieldManager import AirfieldManager


class FlownDistanceCalculator:
    RUN_INTERVAL = 10  # [s]
    running = False

    def __init__(self):
        print(f"[INFO] FlownDistanceCalculator scheduled to run every {self.RUN_INTERVAL}s.")
        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)

    def __del__(self):
        self.influxDb.client.close()

    """
    @param addr: ogn ID with prefix OGN/ICA/FLR
    """
    def _calcFlownDistance(self, addr: str, startTs: int, endTs: int):
        totalDist = 0

        q = f"SELECT lat, lon FROM pos WHERE addr='{addr}' AND time >= {startTs}000000000 AND time <= {endTs}000000000"
        rs = self.influxDb.client.query(query=q)
        if rs:
            prevLat = prevLon = curLat = curLon = None

            for row in rs.get_points():
                curLat = radians(row.get('lat', None))
                curLon = radians(row.get('lon', None))
                if not prevLat:
                    prevLat = curLat
                    prevLon = curLon
                    continue

                dist = AirfieldManager.getDistanceInKm(lat1=prevLat, lon1=prevLon, lat2=curLat, lon2=curLon)
                totalDist += dist

                prevLat = curLat
                prevLon = curLon

        else:
            print(f"[WARN] No influx data for '{addr}' between {startTs} and {endTs}.")

        return totalDist

    def calcDistances(self):
        if self.running:    # still running from the last cron call..
            return

        self.running = True
        updateSqls = []

        strSql = f"SELECT e.id, e.address, e.takeoff_ts, e.landing_ts, ddb.device_type " \
                 f"FROM logbook_entries as e " \
                 f"JOIN ddb ON ddb.device_id = e.address " \
                 f"WHERE e.flown_distance is null;"

        addressPrefixes = {'O':'OGN', 'I':'ICA', 'F':'FLR'}
        with DbSource(dbConnectionInfo).getConnection() as cur:
            cur.execute(strSql)

            for row in cur:
                entryId, address, takeoffTs, landingTs, addressType = row
                if not address or not takeoffTs or not landingTs:
                    continue

                dist = round(self._calcFlownDistance(addr=f"{addressPrefixes[addressType]}{address}", startTs=takeoffTs, endTs=landingTs))
                print(f"[INFO] Flown dist for '{address}' is {dist} km.")

                sql = f"UPDATE logbook_entries SET flown_distance={round(dist)} WHERE id = {entryId};"
                updateSqls.append(sql)

        if len(updateSqls) > 0:
            with DbSource(dbConnectionInfo).getConnection() as cur:
                for sql in updateSqls:
                    cur.execute(sql)
            print(f"[INFO] Updated {len(updateSqls)} flown distance(s)")

        self.running = False


if __name__ == '__main__':
    addr = 'OGNC35001'
    startTs = 1623351592
    endTs = 1623351717

    calc = FlownDistanceCalculator()
    # dist = calc._calcFlownDistance(addr=addr, startTs=startTs, endTs=endTs)
    # print('dist:', round(dist))
    calc.calcDistances()

    print("KOHEU.")
