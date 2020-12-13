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
        self.airfields = []

        with open(AIRFIELDS_FILE, 'r') as f:
            j = json.load(f)
            for item in j:
                ar = AirfieldRecord(item)
                self.airfields.append(ar)

        print(f"[INFO] num airfields: {len(self.airfields)}")

        # sort airfields by latitude:
        self.airfields.sort(key=lambda af: af.lat)
        # get airfields country codes:
        self.afCountryCodes = self._getCountryCodes(self.airfields)
        # split into four sections for faster lookup:
        self.airfields = self._splitAirfieldsIntoQuadrants(self.airfields)

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

            if endI - startI <= 80:
                break

            n += 1
            if n > 80:
                break

        for rec in airfields[startI:endI]:
            dist = AirfieldManager.getDistanceInKm(latRad, lonRad, rec.lat, rec.lon)
            if dist < minDist:
                minDist = dist
                code = rec.code

        if minDist < 4:  # [km]
            return code
        else:
            return None


if __name__ == '__main__':
    am = AirfieldManager()

    # LKNA
    # lat = 49.16
    # lon = 16.11

    # lat = 49.3697147
    # lon = 16.1141575

    # lat = 50.32798
    # lon = 15.95643

    # Poznan EPPK:
    # lat = 52.4335667
    # lon = 17.0384183
    lat = 52.4396
    lon = 17.0553

    # Naromine YNRM
    lat = -32.2144
    lon = 148.2247

    icao = am.getNearest(lat, lon)
    print(icao)
