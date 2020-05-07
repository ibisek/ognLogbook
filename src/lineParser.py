
from enum import Enum

from beaconParser import BeaconParser


class AircraftStatus(Enum):
    onGround = 0
    airborne = 1


class BeaconParsingException(Exception):
    """Base class for exceptions in this module."""
    pass


if __name__ == '__main__':

    bp = BeaconParser()

    fn = '../data/1.line'

    with open(fn, 'r') as f:
        line = f.read()
        # parseLine(line)
        bp.processBeacon(line)

    print('KOHEU.')
