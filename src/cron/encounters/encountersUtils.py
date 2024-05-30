
from datetime import datetime, timezone

from influxdb.resultset import ResultSet

from math import ceil, floor
from position import Position
from sector import Sector, NUM_DECIMALS


def roundNearest(value, multiple):
    return round(value / multiple) * multiple


def roundNearestDown(value, multiple):
    return floor(value / multiple) * multiple


def roundNearestUp(value, multiple):
    return ceil(value / multiple) * multiple


def rowIntoPosition(row: dict) -> Position:
    pos = Position(ts=int(datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()), addr=row['addr'], lat=row['lat'],
                   lon=row['lon'], alt=row['alt'])

    return pos


def splitIntoSectors(rs: ResultSet) -> []:
    sectors = {}    # 'latlon' -> sector/tile containing current flight positions

    currentSector = None
    for row in rs.get_points():
        pos = rowIntoPosition(row)
        if not currentSector or not currentSector.fits(pos.lat, pos.lon):
            roundedLat = round(pos.lat, NUM_DECIMALS)
            roundedLon = round(pos.lon, NUM_DECIMALS)

            # find a sector if already created/existing..
            key = f'{roundedLat}{roundedLon}'
            currentSector = sectors.get(key, None)

            if not currentSector:   # ..or create a new one
                currentSector = Sector(lat=pos.lat, lon=pos.lon)
                sectors[key] = currentSector

        currentSector.append(pos)

    return list(sectors.values())
