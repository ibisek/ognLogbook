"""
A cron service to lookup encounters for each finished flight.
2nd version not using influxdb extensively by caching data in memory.

Needs to be executed in separate process due to performance reasons.
"""

from math import sqrt, pow
from datetime import datetime, timedelta
import sys
from time import sleep
from random import randint

from airfieldManager import AirfieldManager
import dataStructures

from configuration import INFLUX_DB_HOST, INFLUX_DB_NAME
from dao.encountersDao import getEncounterQueueItems, delEncountersQueueItem, Encounter, save, callEncountersPostLookup
from dao.logbookDao import getFlight, getFlightIdForDevIdAndTs
from db.InfluxDbThread import InfluxDbThread

from cache import Cache
from encountersUtils import splitIntoSectors
from sector import Sector
from utils import splitAddress


BATCH_SIZE = 10


class EncountersLookup:
    RUN_INTERVAL = 60  # [s]
    running = False

    def __init__(self):
        print(f"[INFO] EncountersLookup scheduled to run every {self.RUN_INTERVAL}s.")
        self.influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)
        self.cache = Cache()
        # TODO + permanent storage

    def __del__(self):
        self.influxDb.client.close()

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

    def _findOthers(self, ownAddr: str, sector: Sector):  # -> list[Position]:
        others = []

        for ts in range(sector.startTs, sector.endTs+1):
            others.extend(self.cache.list(ts=ts, sectorAddr=sector.addr, omitDeviceAddr=ownAddr))

        return others

    @staticmethod
    def _findNearest(myPositions: list, otherPositions: list) -> int:  # list[Position]
        LIMIT_DIST = 800    # [m]
        LIMIT_TIME = 40     # [s]
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
        for encQItem in encounterQItems:
            batchCounter += 1
            flight = getFlight(flightId=encQItem.flightId)

            self.cache.ensureAllDataInCache(fromTs=flight.takeoff_ts, toTs=flight.landing_ts)

            # load own flight track data:
            ownAddr = f"{dataStructures.addressPrefixes[flight.address_type]}{flight.address}"
            q = f"SELECT time, addr, lat, lon, alt FROM pos WHERE addr='{ownAddr}' AND gs > 80 AND time >= {flight.takeoff_ts}000000000 AND time <= {flight.landing_ts}000000000 ORDER BY time;"
            rs = self.influxDb.query(q)
            if not rs:  # no data for this flight
                delEncountersQueueItem(encQItem)
                continue

            alreadyEncounteredAirplanes = {}    # device_id -> True; only first contact will be stored
            mySectors: list[Sector] = splitIntoSectors(rs)
            for sector in mySectors:
                # print(f"[INFO] SECTOR addr:{sector.addr} dt: {sector.endTs - sector.startTs} numPositions: {len(sector.positions)}")

                # Was there something else in the same sector during the same time-window?
                otherPositions = self._findOthers(ownAddr=ownAddr, sector=sector)
                if len(otherPositions) > 0:
                    otherPositionsInSectorByAddr: dict = self._splitByAddr(otherPositions)
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
            dt = datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S")
            print(f"[INFO] {dt} Analyzed {batchCounter} flights in {round(runTime)}s while discovered {encountersCounter} encounter(s).")

        return batchCounter + 1

    @staticmethod
    def doPostLookup():
        ts = int((datetime.utcnow() - timedelta(hours=6)).timestamp())
        callEncountersPostLookup(startTs=ts)


if __name__ == '__main__':
    task = EncountersLookup()
    while True:
        numProcessed = task.doLookup()
        if numProcessed < BATCH_SIZE:
            sleep(10)

        if randint(0, 10) > 8:
            task.doPostLookup()

    print('KOHEU.')

