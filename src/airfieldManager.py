import sys
import json
from math import degrees, radians, sin, cos, acos

from copy import deepcopy
from typing import Dict, List

from configuration import AIRFIELDS_FILE
from dataStructures import AirfieldRecord, Units
from experimental.nearestGeoPointFinder import NearestGeoPointFinder


class AirfieldManager(object):  # , metaclass=Singleton

    MIN_DIST_FROM_AIRFIELD = 5

    __slots__ = ('airfields', 'airfieldsDict', 'afCountryCodes', 'afCodes', 'finder')

    def __init__(self):
        self.airfields, self.airfieldsDict = self.loadAirfieldsFromFile()

        self.finder = NearestGeoPointFinder(records=deepcopy(self.airfields))

        # self.airfields.sort(key=lambda af: af.lat)    # sort airfields by latitude
        self.airfields.sort(key=lambda af: af.lon)      # ordering by lon gives better & faster results
        # get airfields country codes:
        self.afCountryCodes = self._getCountryCodes(self.airfields)
        # extract all airfields codes:
        self.afCodes = self._getAirfieldCodes(self.airfields)
        # split into four sections for faster lookup:
        self.airfields = self._splitAirfieldsIntoQuadrants(self.airfields)

    @staticmethod
    def loadAirfieldsFromFile():
        airfields = []
        airfieldsDict = {}

        with open(AIRFIELDS_FILE, 'r') as f:
            j = json.load(f)
            for item in j:
                ar = AirfieldRecord(item)
                airfields.append(ar)
                airfieldsDict[ar.code] = ar

        print(f"[INFO] num airfields: {len(airfields)}")

        return airfields, airfieldsDict

    @staticmethod
    def _getCountryCodes(airfields: List[AirfieldRecord]) -> Dict:
        """
        Used on homepage to identify meaning of searched string -> ICAO code vs. airplane's registration
        :param airfields:
        :return: dict(keys) of airfields' country codes (LK, ..)
        """
        d = {}
        for af in airfields:
            code2 = af.code[:2]
            if code2 not in d:
                d[code2] = 1

        return d

    @staticmethod
    def _getAirfieldCodes(airfields: List[AirfieldRecord]) -> Dict:
        """
        Used on homepage to identify meaning of searched string is an ICAO (or alike) code or airplane's registration
        :param airfields:
        :return: dict(keys) of full airfields' CODES
        """
        d = {}
        for af in airfields:
            code = af.code
            d[code] = True

        return d

    @staticmethod
    def _splitAirfieldsIntoQuadrants(airfields: List[AirfieldRecord]) -> Dict:
        """
        Splits AirfieldRecords into quadrants - NE, NW, SE, SW for faster lookup.
        :param airfields:
        :return: dict addressable as d[latSign][lonSign] -> [] of AirfieldRecord-s
        """
        afDict = {1: {1: [], -1: []}, -1: {1: [], -1: []}}

        for af in airfields:
            latSign = 1 if af.lat >= 0 else -1
            lonSign = 1 if af.lon >= 0 else -1

            afDict[latSign][lonSign].append(af)

        return afDict

    @staticmethod
    def getDistanceInKm(lat1: float, lon1: float, lat2: float, lon2: float):
        """
        :param lat1: in radians (!)
        :param lon1: in radians (!)
        :param lat2: in radians (!)
        :param lon2: in radians (!)
        :return: ICAO code of the nearest airfield
        """
        arg = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2 - lon1)
        if arg >= 1.0:
            return 0

        R = 6371  # km
        dist = acos(arg) * R

        return dist

    def getNearest2(self, lat, lon, units: Units = Units.DEG, calcDistance=False):
        """
        :param lat: in degrees
        :param lon: in degrees
        :return: nearest ICAO code or None
        """
        if not lat or not lon:
            return None, None

        record, distanceKm = self.finder.findNearest(lat, lon, units=units, calcDistance=calcDistance)

        return record.code, distanceKm

    def getNearest(self, lat, lon, units: Units = Units.DEG):
        """
        :param lat: in degrees
        :param lon: in degrees
        :param units explicit DEG/RAD, default DEG
        :return: nearest ICAO code or None
        """
        if not lat or not lon:
            return None

        minDist = 99999999999999
        code = None

        if units == Units.DEG:
            latRad = radians(lat)
            lonRad = radians(lon)
        else:
            latRad = lat
            lonRad = lon

        # pick the appropriate airfields list (NE / NW / SE / SW):
        latSign = 1 if latRad >= 0 else -1
        lonSign = 1 if lonRad >= 0 else -1
        airfields = self.airfields[latSign][lonSign]

        rangeLimit = 8000 if latSign == 1 and lonSign == -1 else 100  # in Canada there a too many strips in narrow latitude band
        # TODO the  look-up algo needs to be fixed!

        startI = 0
        endI = len(airfields)
        n = 0
        while True:
            i = startI + int((endI - startI) / 2)
            if lonRad < airfields[i].lon:
                endI = i
            else:
                startI = i

            if endI - startI <= rangeLimit:
                break

            n += 1
            if n > 100:
                break

        for rec in airfields[startI:endI + 1]:  # the +1 makes a HUGE difference - the location is often at the last index position(!)
            dist = AirfieldManager.getDistanceInKm(latRad, lonRad, rec.lat, rec.lon)
            if dist < minDist:
                minDist = dist
                code = rec.code

        if minDist < MIN_DIST_FROM_AIRFIELD:  # [km]
            return code
        else:
            return None

    def xxx_remove(self, code):
        rec = self.airfieldsDict.get(code, None)
        if not rec:
            return None

        # pick the appropriate airfields list (NE / NW / SE / SW):
        latSign = 1 if rec.lat >= 0 else -1
        lonSign = 1 if rec.lon >= 0 else -1

        airfieldSlice = self.airfields[latSign][lonSign]
        airfieldSlice.remove(rec)

        return rec

    def xxx_return(self, rec: AirfieldRecord):
        # pick the appropriate airfields list (NE / NW / SE / SW):
        latSign = 1 if rec.lat >= 0 else -1
        lonSign = 1 if rec.lon >= 0 else -1

        airfieldSlice = self.airfields[latSign][lonSign]
        airfieldSlice.append(rec)

    def get(self, code: str) -> AirfieldRecord:
        return self.airfieldsDict.get(code, None)

    def saveIntoFile(self, filepath: str):
        """
        Stores current airfields into a specified file.
        :param filepath
        """

        with open(filepath, 'w') as f:
            l = list()
            for code, ar in self.airfieldsDict.items():
                d = dict()
                d['code'] = ar.code
                d['lat'] = float(f"{degrees(ar.lat):.4f}")
                d['lon'] = float(f"{degrees(ar.lon):.4f}")
                if ar.alt != 0:
                    d['alt'] = int(ar.alt)

                l.append(d)

            # sort the list by latitude:
            l.sort(key=lambda x: x['lat'])

            j = json.dumps(l)
            f.write(j)


if __name__ == '__main__':
    am = AirfieldManager()

    recs = []
    recs.append(AirfieldRecord({'lat': 49.16, 'lon': 16.11, 'code': 'LKNA'}))
    recs.append(AirfieldRecord({'lat': 52.4396, 'lon': 17.0553, 'code': 'EPPK'}))
    recs.append(AirfieldRecord({'lat': -32.2144, 'lon': 148.2247, 'code': 'YNRM'}))
    recs.append(AirfieldRecord({'lat': 47.2620200, 'lon': 11.3483200, 'code': 'LOWI'}))
    recs.append(AirfieldRecord({'lat': -32.5488500, 'lon': 151.0252500, 'code': 'YWKW'}))
    recs.append(AirfieldRecord({'lat': 43.7535000, 'lon': -79.8711000, 'code': 'CNC3'}))    # lehce bokem podle db ale najde
    # recs.append(AirfieldRecord({'lat': , 'lon': , 'code': ''}))

    for rec in recs:
        # nearestCode = am.getNearest(degrees(rec.lat), degrees(rec.lon))
        nearestCode, distKm = am.getNearest2(degrees(rec.lat), degrees(rec.lon), calcDistance=True)
        nearest = am.get(nearestCode)
        match = rec.code == nearest.code
        out = sys.stderr if not match else sys.stdout
        print(f"match: {match}, {rec.code} -> found: {nearest.code} {distKm} km apart", file=out)

    # am.listInRange(49.1611, 49.1822, 16.4011, 16.9001)

