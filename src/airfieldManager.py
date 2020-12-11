
import json
import math

from singleton import Singleton


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

        with open('../data/airfields.json', 'r') as f:
            j = json.load(f)
            for item in j:
                ar = AirfieldRecord(item)
                self.airfields.append(ar)

        # sort airfields by latitude:
        self.airfields.sort(key=lambda af: af.lat)

        print(f"[INFO] num airfields: {len(self.airfields)}")

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

        startI = 0
        endI = len(self.airfields)
        n = 0
        while True:
            i = startI + int((endI-startI) / 2)
            if latRad < self.airfields[i].lat:
                endI = i
            else:
                startI = i

            if endI - startI <= 200:
                break

            n += 1
            if n > 200:
                break

        for rec in self.airfields[startI:endI]:
            dist = AirfieldManager.getDistanceInKm(latRad, lonRad, rec.lat, rec.lon)
            if dist < minDist:
                minDist = dist
                code = rec.code

        if minDist < 4:   # [km]
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

    icao = am.getNearest(lat, lon)
    print(icao)
