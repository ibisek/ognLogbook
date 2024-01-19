import decimal

from configuration import dbConnectionInfo
from db.DbSource import DbSource

from collections import namedtuple

EncounterQueueItem = namedtuple('EncounterQueueItem', ['id', 'flightId'])


class Encounter:
    def __init__(self, ts: int, addr: str, alt: int, flight_id: int,
                 dist: int,
                 other_addr: str, other_lat: float, other_lon: float, other_alt: int,
                 id: int = None, other_flight_id: int = None):
        self.id = id

        self.ts = ts
        self.addr = addr    # e.g. O123456, I123456, ..
        self.flight_id = flight_id
        self.alt = alt      # [m]

        self.dist = dist    # [m]

        self.other_addr = other_addr
        self.other_flight_id = other_flight_id
        self.other_lat = other_lat
        self.other_lon = other_lon
        self.other_alt = other_alt  # [m]

        self.dirty = False

    def serialize(self):
        d = self.__dict__
        del d['id']
        del d['dirty']

        for k, v in d.items():
            if type(v) == decimal.Decimal:
                d[k] = float(v)

        return d


def getEncounterQueueItems(limit: int = 1) -> []:
    strSql = f"SELECT * FROM encounters_q ORDER BY id LIMIT {limit};"

    qItems = []
    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
        cur.execute(strSql)
        rows = cur.fetchall()

        for row in rows:
            id = row[0]
            flightId = row[1]

            eqi = EncounterQueueItem(id=id, flightId=flightId)
            qItems.append(eqi)

    return qItems


def delEncountersQueueItem(item: EncounterQueueItem):
    strSql = f"DELETE FROM encounters_q WHERE id={item.id};"

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
        cur.execute(strSql)


def listEncounters(flightId: int) -> []:

    strSql = f"SELECT id, ts, addr, alt, dist, other_addr, other_flight_id, other_lat, other_lon, other_alt " \
             f"FROM encounters WHERE flight_id={flightId};"

    encounters = []

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
        cur.execute(strSql)
        rows = cur.fetchall()
        for row in rows:
            id = row[0]
            ts = row[1]
            addr = row[2]
            alt = row[3]
            dist = row[4]
            other_addr = row[5]
            other_flight_id = row[6]
            other_lat = row[7]
            other_lon = row[8]
            other_alt = row[9]

            enc = Encounter(id=id, ts=ts, addr=addr, alt=alt, flight_id=flightId, dist=dist, other_addr=other_addr, other_flight_id=other_flight_id, other_lat=other_lat, other_lon=other_lon, other_alt=other_alt)
            encounters.append(enc)

    return encounters


def listEncountersWithRegistration(flightId: int) -> []:

    strSql = f"SELECT e.id, e.ts, e.addr, e.alt, e.dist, e.other_addr, e.other_flight_id, e.other_lat, e.other_lon, " \
             f"e.other_alt, d.aircraft_registration, d.aircraft_cn, d.aircraft_type " \
             f"FROM encounters AS e " \
             f"LEFT JOIN ddb AS d ON SUBSTR(e.addr, 1, 1)=d.device_type AND SUBSTR(e.addr, 2)=d.device_id " \
             f"WHERE e.flight_id={flightId};"

    encounters = []

    with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
        cur.execute(strSql)
        rows = cur.fetchall()
        for row in rows:
            id = None   # row[0]
            ts = row[1]
            addr = row[2]
            alt = row[3]
            dist = row[4]
            other_addr = row[5]
            other_flight_id = row[6]
            other_lat = row[7]
            other_lon = row[8]
            other_alt = row[9]
            registration = row[10]
            cn = row[11]
            aircraft_type = row[12]

            enc = Encounter(id=id, ts=ts, addr=addr, alt=alt, flight_id=flightId, dist=dist, other_addr=other_addr, other_flight_id=other_flight_id, other_lat=other_lat, other_lon=other_lon, other_alt=other_alt)
            enc.registration = registration
            enc.cn = cn
            enc.aircraft_type = aircraft_type

            encounters.append(enc)

    return encounters




# def findEncounter(ts: int, addr1: str, addr2: str):
#     addrs = sorted([addr for addr in [addr1, addr2]])
#
#     strSql = f"SELECT id, ts, lat, lon, dev_id_1, dev_id_2, flight_id_1, flight_id_2 " \
#              f"FROM encounters WHERE ts={ts} AND dev_id_1='{addrs[0]}' AND dev_id_2='{addrs[1]}' " \
#              f"LIMIT 1;"
#
#     with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
#         cur.execute(strSql)
#         row = cur.fetchone()
#         if row:
#             id = row[0]
#             ts = row[1]
#             lat = row[2]
#             lon = row[3]
#             dev_id_1 = row[4]
#             dev_id_2 = row[5]
#             flight_id_1 = row[6]
#             flight_id_2 = row[7]
#
#             return Encounter(id=id, ts=ts, lat=lat, lon=lon, dev_id_1=dev_id_1, dev_id_2=dev_id_2, flight_id_1=flight_id_1, flight_id_2=flight_id_2)
#
#     return None


def save(enc: Encounter):
    if not enc.id:  # insert
        otherFlightId = f"{enc.other_flight_id}" if enc.other_flight_id else "null"

        strSql = f"INSERT INTO encounters (ts, addr, flight_id, alt, dist, other_addr, other_flight_id, other_lat, other_lon, other_alt) " \
                 f"VALUES ({enc.ts}, '{enc.addr}', {enc.flight_id}, {round(enc.alt)}, {enc.dist}, " \
                 f"'{enc.other_addr}', {otherFlightId}, {enc.other_lat:.6f}, {enc.other_lon:.6f}, {round(enc.other_alt)});"

        with DbSource(dbConnectionInfo).getConnection().cursor() as cur:
            cur.execute(strSql)

    else:   # update
        # TODO update
        pass

    enc.dirty = False


def listEncountersWithoutOtherFlightId(startTs: int = 0):
    strSQL = f"SELECT id,  ts, other_addr FROM encounters WHERE other_flight_id IS null AND ts > {startTs};"
    # TODO mozna by slo udelat jen updatem v DB?


if __name__ == '__main__':
    encounterQItem = getEncounterQueueItems()
    print('flightId:', encounterQItem)
