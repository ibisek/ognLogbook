from math import radians

from configuration import dbConnectionInfo, INFLUX_DB_HOST, INFLUX_DB_NAME
from db.DbSource import DbSource
from db.InfluxDbThread import InfluxDbThread
from airfieldManager import AirfieldManager


class FlownDistanceCalculator:
    RUN_INTERVAL = 10  # [s]

    def __init__(self):
        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)

    def __del__(self):
        self.influxDb.client.close()

    """
    @param addr: ogn ID with prefix OGN/ICA/FLR
    """
    def _calcFlownDistance(self, addr: str, startTs: int, endTs: int):
        totalDist = 0

        q = f"SELECT lat, lon FROM pos WHERE addr='{addr}' and time >= {startTs}000000000 and time <= {endTs}000000000"
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

        return totalDist

    def calcDistances(self):
        strSql = f"SELECT id, address, takeoff_ts, landing_ts " \
                 f"FROM logbook_entries " \
                 f"WHERE flown_distance is null;"

        with DbSource(dbConnectionInfo).getConnection() as cur:
            cur.execute(strSql)

            for row in cur:
                entryId, address, takeoffTs, landingTs = row
                dist = self._calcFlownDistance(addr=address, startTs=takeoffTs, endTs=landingTs)

                sql = f"UPDATE logbook_entries SET flown_distance={round(dist)} WHERE id = {entryId}'"
                # TODO update distance in the record
                print(666)

        # TODO select all entries where flown_dist is null (all processed will have this value set to 0 even if not known)
        addr = 'xxx'
        starTs = 0
        endTs = 0
        dist = self._calcFlownDistance(addr=addr, startTs=startTs, endTs=endTs)
        # TODO store calculated distance


if __name__ == '__main__':
    addr = 'OGNC35001'
    startTs = 1623351592
    endTs = 1623351717

    calc = FlownDistanceCalculator()
    dist = calc._calcFlownDistance(addr=addr, startTs=startTs, endTs=endTs)
    print('dist:', round(dist))
