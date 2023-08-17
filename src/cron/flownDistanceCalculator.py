"""
A cron service to calculate real flown distance (point-to-point) for each flight.
"""

from math import radians

from configuration import dbConnectionInfo, INFLUX_DB_HOST, INFLUX_DB_NAME, INFLUX_DB_NAME_PERMANENT_STORAGE
from dao.permanentStorage import PermanentStorageFactory
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
        self.influxDbPs = InfluxDbThread(dbName=INFLUX_DB_NAME_PERMANENT_STORAGE, host=INFLUX_DB_HOST)

        self.permanentStorages = dict()

    def __del__(self):
        self.influxDb.client.close()

    """
    @param addr: ogn ID with prefix OGN/ICA/FLR
    @param addressType: O/I/F
    """

    def _calcFlownDistance(self, address: str, addressType: str, startTs: int, endTs: int) -> (int, int):
        totalDist = 0
        maxAlt = 0

        influxInstance = self.influxDb
        permanentStorage = self.permanentStorages.setdefault(addressType, PermanentStorageFactory.storageFor(addressType))
        if permanentStorage.eligible4ps(address):
            influxInstance = self.influxDbPs

        addrWithPrefix = f"{addressPrefixes[addressType]}{address}"

        q = f"SELECT lat, lon, alt FROM pos WHERE addr='{addrWithPrefix}' AND time >= {startTs}000000000 AND time <= {endTs}000000000"
        rs = influxInstance.client.query(query=q)
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

                alt = row.get('alt', 0)
                if alt > maxAlt:
                    maxAlt = alt

        else:
            print(f"[WARN] No influx data for '{address}' between {startTs} and {endTs}.")

        return round(totalDist), round(maxAlt)

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

                dist, maxAlt = self._calcFlownDistance(address=address, addressType=addressType, startTs=takeoffTs, endTs=landingTs)
                print(f"[INFO] Flown dist for '{addressPrefixes[addressType]}{address}' is {dist} km with maxAlt of {maxAlt} m")

                sql = f"UPDATE logbook_entries SET flown_distance={dist}, max_alt={maxAlt} WHERE id = {entryId};"
                updateSqls.append(sql)

        if len(updateSqls) > 0:
            with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
                for sql in updateSqls:
                    cur.execute(sql)
            print(f"[INFO] Updated {len(updateSqls)} flown distance(s)")

        self.running = False


if __name__ == '__main__':
    calc = FlownDistanceCalculator()

    addr = 'C35008'
    addrType = 'O'
    startTs = 1692252000
    endTs = 1692302237
    dist, maxAlt = calc._calcFlownDistance(address=addr, addressType=addrType, startTs=startTs, endTs=endTs)
    print(f'dist: {dist} km; maxAlt: {maxAlt} m')

    # calc.calcDistances()

    print("KOHEU.")
