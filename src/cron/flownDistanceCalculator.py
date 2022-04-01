"""
A cron service to calculate real flown distance (point-to-point) for each flight.
"""

from math import radians

from configuration import dbConnectionInfo, INFLUX_DB_HOST, INFLUX_DB_NAME
from db.DbSource import DbSource
from db.InfluxDbThread import InfluxDbThread
from airfieldManager import AirfieldManager
from dataStructures import addressPrefixes


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

        strSql = f"SELECT e.id, e.address, e.address_type, e.takeoff_ts, e.landing_ts " \
                 f"FROM logbook_entries as e " \
                 f"WHERE e.flown_distance is null;"

        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            cur.execute(strSql)

            for row in cur:
                entryId, address, addressType, takeoffTs, landingTs = row
                if not address or not addressType or not takeoffTs or not landingTs:
                    continue

                dist = round(self._calcFlownDistance(addr=f"{addressPrefixes[addressType]}{address}", startTs=takeoffTs, endTs=landingTs))
                print(f"[INFO] Flown dist for '{addressPrefixes[addressType]}{address}' is {dist} km.")

                sql = f"UPDATE logbook_entries SET flown_distance={round(dist)} WHERE id = {entryId};"
                updateSqls.append(sql)

        if len(updateSqls) > 0:
            with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
                for sql in updateSqls:
                    cur.execute(sql)
            print(f"[INFO] Updated {len(updateSqls)} flown distance(s)")

        self.running = False


if __name__ == '__main__':
    calc = FlownDistanceCalculator()

    addr = 'OGN1C2902'
    startTs = 1641542747
    endTs = 1641542876
    dist = calc._calcFlownDistance(addr=addr, startTs=startTs, endTs=endTs)
    print('dist:', round(dist))

    # calc.calcDistances()

    print("KOHEU.")
