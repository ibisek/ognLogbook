"""
Code to extract all (influx) cached traffic around specified coordinates
(typically an airfield) and render it into a map to display traffic patterns in that ATZ.
"""
from math import cos, degrees, radians
from datetime import datetime

import geohash

from airfieldManager import AirfieldManager, AirfieldRecord
from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST, ADDRESS_TYPES, REVERSE_ADDRESS_TYPE_PREFIX
from dao.ddb import DDB, DDBRecord
from db.InfluxDbThread import InfluxDbThread

ddb = DDB.getInstance()
influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST, startThread=False)


def boundingBox(lat, lon, diameter):
    """
    Returns a bounding box centered at (lat, lon) of a given size.
    :param lat  center latitude in degrees
    :param lon  center longitude in degrees
    :param diameter edge length of square in meters
    :returns (minLat, maxLat, minLon, maxLon)
    """

    # Earth's radius in meters
    EARTH_RADIUS = 6378137

    # Half side length
    halfSide = diameter / 2.0

    # Latitude: angular distance in radians
    deltaLat = halfSide / EARTH_RADIUS
    deltaLatDeg = degrees(deltaLat)

    # Longitude: adjust for latitude
    deltaLon = halfSide / (EARTH_RADIUS * cos(radians(lat)))
    deltaLonDeg = degrees(deltaLon)

    minLat = lat - deltaLatDeg
    maxLat = lat + deltaLatDeg
    minLon = lon - deltaLonDeg
    maxLon = lon + deltaLonDeg

    return minLat, maxLat, minLon, maxLon


def coordsForAirfield(airfieldCode: str):
    af: AirfieldRecord = AirfieldManager().airfieldsDict.get(airfieldCode, None)
    return degrees(af.lat), degrees(af.lon)


def _trafficForCoords(lat: float, lon: float):
    RANGE_KM = 5    # [km]

    latRad = radians(lat)
    lonRad = radians(lon)

    gh = geohash.encode(lat, lon, precision=5)  # 4 ~ 30km, 5 ~ 5km, 6 ~ 1km
    neighbouringGhs = geohash.expand(gh)
    ghCond = "".join([f"gh = '{n}' OR " for n in neighbouringGhs]).rstrip('OR ')

    q = f"SELECT time, addr, lat, lon, alt FROM pos WHERE ({ghCond})"

    flights = {}
    ddbRecs = {}

    rs = influxDb.client.query(query=q)
    if rs:
        for row in rs.get_points():
            row['dt'] = datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%SZ')

            dist = AirfieldManager.getDistanceInKm(lat1=latRad, lon1=lonRad, lat2=radians(row['lat']), lon2=radians(row['lon']))
            if dist <= RANGE_KM:    # keep only records within the RANGE; drop the more distant ones
                addr = row['addr']
                l = flights.get(addr, [])
                if len(l) == 0:
                    flights[addr] = l
                l.append(row)

    # fetch appropriate DDB records:
    for addr in flights.keys():
        devType = ADDRESS_TYPES.get(REVERSE_ADDRESS_TYPE_PREFIX.get(addr[:3], 3), 'O')   # 3 = return OGN if unknown
        devId = addr[3:]

        ddbRec: DDBRecord = ddb.get(device_type=devType, device_id=devId)

        if not ddbRec:
            ddbRec = DDBRecord()
            ddbRec.device_type = devType
            ddbRec.device_id = devId

        ddbRecs[addr] = ddbRec

    return flights, ddbRecs


def trafficForAirfieldCode(aifieldCode: str):
    lat, lon = coordsForAirfield(aifieldCode)
    flights, ddbRecs = _trafficForCoords(lat, lon)

    return flights, ddbRecs


if __name__ == '__main__':
    # airfieldCode = 'LKKA'
    # lat, lon = coordsForAirfield(airfieldCode)
    # gh = geohash.encode(lat, lon, precision=5)  # 4 ~ 30km, 5 ~ 5km, 6 ~ 1km
    # print(f"{airfieldCode} GH:", gh)
    # neighbours = geohash.expand(gh)
    # print("NB:", neighbours)

    flights, ddbRecs = trafficForAirfieldCode('LKKA')
