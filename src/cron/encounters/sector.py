
import sys
from math import floor, ceil

from position import Position

# LAT+LON:
#     2 decimals -> square 0.7 x 0.7 km
#     1 decimal -> square 11 x 11 km
#     (at latitude ~ N49)
NUM_DECIMALS = 1
mult = pow(10, NUM_DECIMALS)


class Sector:
    def __init__(self, lat: int, lon: int):

        self.lat_min = floor(lat * mult) / mult
        self.lon_min = floor(lon * mult) / mult
        self.lat_max = ceil(lat * mult) / mult
        self.lon_max = ceil(lon * mult) / mult

        self.addr = Sector.calcSectorAddr(lat=lat, lon=lon)

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

    @staticmethod
    def calcSectorAddr(lat: float, lon: float):
        lat_min = floor(lat * mult) / mult
        lon_min = floor(lon * mult) / mult

        return f"{lat_min}_{lon_min}"
