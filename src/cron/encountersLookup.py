"""
A cron service to lookup encounters for each finished flight.

LAT+LON:
    2 decimals -> square 0.7 x 0.7 km
    1 decimal -> square 11 x 11 km
    (at latitude ~ N49)

Needs to be executed in separate process due to performance reasons.
"""

from math import degrees, radians, floor, ceil, sqrt, pow
from datetime import datetime, timezone
import sys
from time import sleep

from influxdb.resultset import ResultSet

from airfieldManager import AirfieldManager
from configuration import INFLUX_DB_HOST, INFLUX_DB_NAME
from dao.logbookDao import getFlightIdForDevIdAndTs
import dataStructures
from db.InfluxDbThread import InfluxDbThread

from dao.encounters import getEncounterQueueItems, delEncountersQueueItem, Encounter, save
from dao.logbookDao import getFlight

from utils import splitAddress

NUM_DECIMALS = 1
BATCH_SIZE = 10


class Position:
    def __init__(self, ts: int, addr: str, lat: float, lon: float, alt: float):
        self.ts = ts
        self.addr = addr
        self.lat = lat
        self.lon = lon
        self.alt = alt

        self._lat_rad = None
        self._lon_rad = None

    @property
    def lat_rad(self):
        if not self._lat_rad:
            self._lat_rad = radians(self.lat)

        return self._lat_rad

    @property
    def lon_rad(self):
        if not self._lon_rad:
            self._lon_rad = radians(self.lon)

        return self._lon_rad


class Sector:
    def __init__(self, lat: int, lon: int):
        self.lat_min = floor(lat * 10 * NUM_DECIMALS) / 10 * NUM_DECIMALS
        self.lat_max = ceil(lat * 10 * NUM_DECIMALS) / 10 * NUM_DECIMALS
        self.lon_min = floor(lon * 10 * NUM_DECIMALS) / 10 * NUM_DECIMALS
        self.lon_max = ceil(lon * 10 * NUM_DECIMALS) / 10 * NUM_DECIMALS
        # self.lat_min = EncountersLookup.roundNearestDown(lat, 0.05)
        # self.lat_max = self.lat_min + 0.05
        # self.lon_min = EncountersLookup.roundNearestDown(lon, 0.05)
        # self.lon_max = self.lon_min + 0.05

        self.positions = []
        self.startTs = sys.maxsize
        self.endTs = 0

    def fits(self, lat, lon) -> bool:
        # print(f"LAT {lat} into {self.lat_min} -> {self.lat_max}")
        # print(f"LON {lon} into {self.lon_min} -> {self.lon_max}")
        if self.lat_min <= lat < self.lat_max and self.lon_min <= lon < self.lon_max:
            return True
        else:
            return False

    def append(self, pos: Position):
        self.positions.append(pos)

        if self.startTs > pos.ts:
            self.startTs = pos.ts

        if self.endTs < pos.ts:
            self.endTs = pos.ts


class EncountersLookup:
    RUN_INTERVAL = 60  # [s]
    running = False

    def __init__(self):
        print(f"[INFO] EncountersLookup scheduled to run every {self.RUN_INTERVAL}s.")
        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)
        # TODO + permanent storage

    def __del__(self):
        self.influxDb.client.close()

    @staticmethod
    def roundNearest(value, multiple):
        return round(value / multiple) * multiple

    def roundNearestDown(value, multiple):
        return floor(value / multiple) * multiple

    def roundNearestUp(value, multiple):
        return ceil(value / multiple) * multiple

    @staticmethod
    def _rowIntoPosition(row: dict) -> Position:
        pos = Position(ts=int(datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()), addr=row['addr'], lat=row['lat'],
                       lon=row['lon'], alt=row['alt'])

        return pos

    @staticmethod
    def _splitIntoSectors(rs: ResultSet) -> []:
        sectors = []  # list of sectors/tiles containing current flight positions

        currentSector = None
        for row in rs.get_points():
            pos = EncountersLookup._rowIntoPosition(row)
            # roundedLat = round(pos.lat, NUM_DECIMALS)
            # roundedLon = round(pos.lon, NUM_DECIMALS)

            if not currentSector or not currentSector.fits(pos.lat, pos.lon):
                currentSector = Sector(lat=pos.lat, lon=pos.lon)
                sectors.append(currentSector)

            currentSector.append(pos)

        return sectors

    def _findOthers(self, ownAddr: str, sector: Sector):  # -> list[Position]:
        DT = 5  # [s]  a bit larger time window +/-
        q = f"SELECT time, addr, lat, lon, alt FROM pos " \
            f"WHERE lat>={sector.lat_min} AND lat<{sector.lat_max}  " \
            f"AND lon>={sector.lon_min} AND lon<{sector.lon_max} " \
            f"AND addr != '{ownAddr}' " \
            f"AND gs>80 "\
            f"AND time>={sector.startTs - DT}000000000 AND time<={sector.endTs + DT}000000000;"
        rs = self.influxDb.query(q)
        if not rs:
            return []

        others = []
        for row in rs.get_points():
            pos = EncountersLookup._rowIntoPosition(row)
            others.append(pos)

        return others

    @staticmethod
    def _splitByAddr(otherPositions: []):
        """
        :param otherPositions:
        :return: map of addr->[] of positions for each separate airplane
        """
        others = {}  # addr -> [positions]
        for pos in otherPositions:
            others.setdefault(pos.addr, []).append(pos)

        return others

    @staticmethod
    def _findNearest(myPositions: list, otherPositions: list) -> int:  # list[Position]
        LIMIT_DIST = 500    # [m]
        LIMIT_TIME = 10     # [s]
        """
        Nearest fix in distance and time.
        :param myPositions: 
        :param otherPositions: 
        :return: 
        """
        minDist = sys.maxsize
        min_myPos = None
        min_otherPos = None

        for myPos, otherPos in zip(myPositions, otherPositions):
            hDistKm = AirfieldManager.getDistanceInKm(lat1=myPos.lat_rad, lon1=myPos.lon_rad, lat2=otherPos.lat_rad, lon2=otherPos.lon_rad)
            vDistM = abs(myPos.alt - otherPos.alt)
            dist = sqrt(pow(hDistKm * 1000, 2) + pow(vDistM, 2))  # [m]
            dt = abs(myPos.ts - otherPos.ts)
            if dist < minDist and dt <= LIMIT_TIME:
                minDist = dist
                min_myPos = myPos
                min_otherPos = otherPos
        if minDist <= LIMIT_DIST:
            return minDist, min_myPos, min_otherPos
        else:
            return None, None, None

    def doLookup(self):
        if self.running:
            return

        self.running = True
        startTs = datetime.now().timestamp()
        encountersCounter = 0

        encounterQItems = getEncounterQueueItems(limit=BATCH_SIZE)

        batchCounter = 0
        for batchCounter, encQItem in enumerate(encounterQItems):
            flight = getFlight(flightId=encQItem.flightId)

            ownAddr = f"{dataStructures.addressPrefixes[flight.address_type]}{flight.address}"
            q = f"SELECT time, addr, lat, lon, alt FROM pos WHERE addr='{ownAddr}' AND gs > 80 AND time >= {flight.takeoff_ts}000000000 AND time <= {flight.landing_ts}000000000;"
            rs = self.influxDb.query(q)
            if not rs:  # no data for this flight
                delEncountersQueueItem(encQItem)
                continue

            alreadyEncounteredAirplanes = {}    # device_id -> True; only first contact will be stored
            mySectors: list[Sector] = self._splitIntoSectors(rs)
            for sector in mySectors:
                # print(f"[INFO] SECTOR dt: {sector.endTs - sector.startTs} numPositions: {len(sector.positions)}")

                # Was there something else in the same sector during the same time-window?
                otherPositions = self._findOthers(ownAddr=ownAddr, sector=sector)
                if len(otherPositions) > 0:
                    otherPositionsInSectorByAddr: dict = EncountersLookup._splitByAddr(otherPositions)
                    for addr in alreadyEncounteredAirplanes.keys():
                        otherPositionsInSectorByAddr.pop(addr, None)  # remove those with an encounter already recorded

                    # Find the nearest one for each other airplane:
                    for otherAddr, otherPositions in otherPositionsInSectorByAddr.items():
                        if otherAddr in alreadyEncounteredAirplanes:
                            continue  # do not analyse positions for planes we already encountered

                        dist, myPos, otherPos = EncountersLookup._findNearest(sector.positions, otherPositions)
                        if dist:    # conditions for an encounter met
                            # print(f"[INFO] {myPos.addr} seen {otherPos.addr} {dist:.1f} m and {abs(myPos.ts - otherPos.ts)}s apart")
                            ts = myPos.ts if myPos.ts < otherPos.ts else otherPos.ts    # the earlier one

                            # Parse addr + addrTypes:
                            myAddrShortType, _, myAddr = splitAddress(myPos.addr)
                            otherAddrShortType, otherAddrLongType, otherAddr = splitAddress(otherPos.addr)

                            # Lookup current (own) flightId:
                            flightId = getFlightIdForDevIdAndTs(addr=myAddr, addrType=myAddrShortType, ts=myPos.ts)
                            if not flightId:
                                continue    # XXX jak je mozne, ze nenajde sam sebe, kdyz z neho vzniknul?

                            encounter = Encounter(ts=ts, addr=f"{myAddrShortType}{myAddr}", alt=myPos.alt, flight_id=flightId,
                                                  dist=round(dist),
                                                  other_addr=f"{otherAddrShortType}{otherAddr}", other_lat=otherPos.lat, other_lon=otherPos.lon, other_alt=otherPos.alt)

                            # Lookup the other flightId (if already available):
                            encounter.other_flight_id = getFlightIdForDevIdAndTs(addr=otherAddr, addrType=otherAddrShortType, ts=ts)

                            save(encounter)
                            encountersCounter += 1
                            alreadyEncounteredAirplanes[otherAddrLongType+otherAddr] = True

            delEncountersQueueItem(encQItem)

        self.running = False
        if batchCounter > 0:
            runTime = datetime.now().timestamp() - startTs
            print(f"[INFO] Analyzed {batchCounter + 1} flights in {round(runTime)}s while discovered {encountersCounter} encounter(s).")

        return batchCounter + 1

    def doPostLookup(self):
        # TODO dohledat other_flight_ids tam, kde nejsou
        # TODO asi dohledavat jen pro posledni 2 dny..
        pass


if __name__ == '__main__':
    task = EncountersLookup()
    while True:
        numProcessed = task.doLookup()
        if numProcessed < BATCH_SIZE:
            sleep(10)

        task.doPostLookup()

    # task.doPostLookup()

    print('KOHEU.')

