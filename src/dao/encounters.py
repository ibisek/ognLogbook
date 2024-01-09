from datetime import datetime

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


if __name__ == '__main__':
    encounterQItem = getEncounterQueueItem()
    print('flightId:', encounterQItem)
