from influxdb.resultset import ResultSet

from configuration import INFLUX_DB_HOST, INFLUX_DB_NAME
from db.InfluxDbThread import InfluxDbThread
from encountersUtils import rowIntoPosition
from position import Position
from sector import Sector


class Cache:

    def __init__(self):
        self.data = {}     # ts-lan-lon-sector -> { addr -> [positions] }
        self.tsStart = None
        self.tsEnd = None

        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)

    def __del__(self):
        self.influxDb.client.close()

    def _addToData(self, ts: int, sectorAddr: str, pos: Position):
        if ts not in self.data:
            self.data[ts] = {}

        if sectorAddr not in self.data[ts]:
            self.data[ts][sectorAddr] = []

        self.data[ts][sectorAddr].append(pos)

    def _populateCache(self, q: str):
        rs: ResultSet = self.influxDb.query(q)
        if not rs:  # no data for this flight
            return

        for row in rs.get_points():
            pos: Position = rowIntoPosition(row)
            sectorAddr = Sector.calcSectorAddr(lat=pos.lat, lon=pos.lon)
            self._addToData(ts=pos.ts, sectorAddr=sectorAddr, pos=pos)

    def ensureAllDataInCache(self, fromTs: int, toTs: int) -> bool:
        if not self.tsStart or not self.tsEnd:  # initial data fetch
            q = f"SELECT time, addr, lat, lon, alt FROM pos WHERE gs > 80 AND time >= {fromTs}000000000 AND time <= {toTs}000000000;"
            self._populateCache(q)

            self.tsStart = fromTs
            self.tsEnd = toTs

        else:
            if fromTs < self.tsStart:
                q = f"SELECT time, addr, lat, lon, alt FROM pos WHERE gs > 80 AND time >= {fromTs}000000000 AND time < {self.tsStart}000000000;"
                self._populateCache(q)

                self.tsStart = fromTs

            if toTs > self.tsEnd:
                q = f"SELECT time, addr, lat, lon, alt FROM pos WHERE gs > 80 AND time > {self.tsEnd}000000000 AND time <= {toTs}000000000;"
                self._populateCache(q)

                self.tsEnd = toTs

        # TODO jednou za cas odmazat data starsi nez X hodin

    def list(self, ts: int, sectorAddr: str, omitDeviceAddr: str) -> [Position]:
        positions = self.data.get(ts, {}).get(sectorAddr, [])
        positions = [pos for pos in positions if pos.addr != omitDeviceAddr]

        return positions
