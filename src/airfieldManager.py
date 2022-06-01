import sys
import json
import math

from typing import Dict, List
from configuration import AIRFIELDS_FILE


class AirfieldRecord(object):

    def __init__(self, map: dict):
        self.lat = math.radians(map['lat'])
        self.lon = math.radians(map['lon'])
        self.code = map['code']

    def __str__(self):
        return f'#AirfieldRecord: {self.code}; lat:{self.lat:.4f}; lon:{self.lon:.4f}'


class AirfieldManager(object):  # , metaclass=Singleton

    def __init__(self):
        self.airfields, _ = self.loadAirfieldsFromFile()

        # sort airfields by latitude:
        self.airfields.sort(key=lambda af: af.lat)
        # get airfields country codes:
        self.afCountryCodes = self._getCountryCodes(self.airfields)
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
        arg = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
        if arg >= 1.0:
            return 0

        R = 6371  # km
        dist = math.acos(arg) * R

        return dist

    def getNearest(self, lat, lon):
        """
        :param lat: in degrees
        :param lon: in degrees
        :return: nearest ICAO code or None
        """
        if not lat or not lon:
            return None

        minDist = 99999999999999
        code = None

        latRad = math.radians(lat)
        lonRad = math.radians(lon)

        # pick the appropriate airfields list (NE / NW / SE / SW):
        latSign = 1 if latRad >= 0 else -1
        lonSign = 1 if lonRad >= 0 else -1
        airfields = self.airfields[latSign][lonSign]

        startI = 0
        endI = len(airfields)
        n = 0
        while True:
            i = startI + int((endI - startI) / 2)
            if latRad < airfields[i].lat:
                endI = i
            else:
                startI = i

            if endI - startI <= 100:
                break

            n += 1
            if n > 100:
                break

        for rec in airfields[startI:endI + 1]:  # the +1 makes a HUGE difference - the location is often at the last index position(!)
            dist = AirfieldManager.getDistanceInKm(latRad, lonRad, rec.lat, rec.lon)
            if dist < minDist:
                minDist = dist
                code = rec.code

        if minDist < 5:  # [km]
            return code
        else:
            return None


if __name__ == '__main__':
    am = AirfieldManager()

    recs = []
    recs.append(AirfieldRecord({'lat': 49.16, 'lon': 16.11, 'code': 'LKNA'}))
    recs.append(AirfieldRecord({'lat': 52.4396, 'lon': 17.0553, 'code': 'EPPK'}))
    recs.append(AirfieldRecord({'lat': -32.2144, 'lon': 148.2247, 'code': 'YNRM'}))
    recs.append(AirfieldRecord({'lat': 47.2620200, 'lon': 11.3483200, 'code': 'LOWI'}))
    recs.append(AirfieldRecord({'lat': -32.5488500, 'lon': 151.0252500, 'code': 'YWKW'}))
    # recs.append(AirfieldRecord({'lat': , 'lon': , 'code': ''}))

    for rec in recs:
        icao = am.getNearest(math.degrees(rec.lat), math.degrees(rec.lon))
        match = rec.code == icao
        out = sys.stderr if not match else sys.stdout
        print(f"match: {match}, {rec.code} -> found: {icao}", file=out)

    am.listInRange(49.1611, 49.1822, 16.4011, 16.9001)

