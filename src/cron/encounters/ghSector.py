"""
GEOHASH-based sector (square).
"""

import sys

from position import Position


class GhSector:
    def __init__(self, gh: str):

        self.gh = gh

        self.positions = []
        self.othersPositions = {}   # addr -> [pos]

        self.startTs = sys.maxsize
        self.endTs = 0

        self.minAlt = sys.maxsize
        self.maxAlt = 0

    def append(self, pos: Position):
        self.positions.append(pos)

        if self.startTs > pos.ts:
            self.startTs = pos.ts

        if self.endTs < pos.ts:
            self.endTs = pos.ts

        if pos.alt < self.minAlt:
            self.minAlt = pos.alt

        if pos.alt > self.maxAlt:
            self.maxAlt = pos.alt

    def appendOtherPosition(self, pos:Position):
        positions = self.othersPositions.get(pos.addr, [])
        positions.append(pos)

        if len(positions) == 1:     # new entry in list
            self.othersPositions[pos.addr] = positions

