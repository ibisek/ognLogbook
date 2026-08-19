"""
More sophisticated geo-distace finder than the original one ;)
"""

import numpy as np

from math import radians
from scipy.spatial import KDTree

from dataStructures import AirfieldRecord, Units

EARTH_RADIUS_KM = 6378.0
EARTH_RADIUS_METERS = EARTH_RADIUS_KM * 1000


def recordToCartesian3d(lat_deg, lon_deg, alt_meters=0.0):
    """
    Converts (lat, lon, alt) to true 3D Cartesian coordinates (x, y, z) in meters.
    """
    lat_rad = np.radians(np.asarray(lat_deg, dtype=np.float64))
    lon_rad = np.radians(np.asarray(lon_deg, dtype=np.float64))
    alt = np.asarray(alt_meters, dtype=np.float64)

    r = EARTH_RADIUS_METERS + alt

    x = r * np.cos(lat_rad) * np.cos(lon_rad)
    y = r * np.cos(lat_rad) * np.sin(lon_rad)
    z = r * np.sin(lat_rad)

    if np.ndim(lat_deg) == 0:
        return np.array([x, y, z], dtype=np.float64)

    return np.column_stack((x, y, z))


def chordDistanceToKm(chord_dist, radius=EARTH_RADIUS_KM):
    """Converts 3D Euclidean distance to spherical ground distance in km."""
    chord_dist = np.clip(chord_dist, 0.0, 2.0)
    return 2.0 * radius * np.arcsin(chord_dist / 2.0)


class NearestGeoPointFinder:
    def __init__(self, records: list[AirfieldRecord]):
        self.records = records

        # Extract lat/lon arrays in DEGREES
        lats = np.array([record.lat_deg for record in records])
        lons = np.array([record.lon_deg for record in records])

        # Convert dataset to 3D surface Cartesian points
        self.points_3d = recordToCartesian3d(lats, lons)
        self.tree = KDTree(self.points_3d)

    def findNearest(self, lat: float, lon: float, alt: float = 0.0, units: Units = Units.DEG, calcDistance=False):
        """
        Finds the nearest record in the dataset for a given query point.
        """
        # Convert input to DEGREES if passed as RADIANS
        if units is Units.RAD:
            lat_deg = np.degrees(lat)
            lon_deg = np.degrees(lon)
        else:
            lat_deg = lat
            lon_deg = lon

        query3d = recordToCartesian3d(lat_deg, lon_deg)
        _, nearest_idx = self.tree.query(query3d)

        matchedRecord = self.records[nearest_idx]

        distanceKm = None
        if calcDistance:
            # Convert both points to radians before calling _haversineKm
            lat1_rad, lon1_rad = radians(lat_deg), radians(lon_deg)
            lat2_rad, lon2_rad = matchedRecord.lat_rad, matchedRecord.lon_rad

            distanceKm = self._haversineKm(lat1_rad, lon1_rad, lat2_rad, lon2_rad)

        return matchedRecord, distanceKm

    @staticmethod
    def _haversineKm(lat1_rad, lon1_rad, lat2_rad, lon2_rad):
        """
        Exact great-circle distance on Earth surface in kilometers.
        Inputs MUST be in radians.
        """
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
        a_clipped = np.clip(a, 0.0, 1.0)

        return float(round(EARTH_RADIUS_KM * 2.0 * np.arcsin(np.sqrt(a_clipped)), 3))


# if __name__ == '__main__':
#     airfields, _ = AirfieldManager.loadAirfieldsFromFile()
#
#     finder = NearestGeoPointFinder(records=airfields)
#
#     # target_lat, target_lon = 45.4861, -75.0961  # CNF3
#     # target_lat, target_lon = 45.5833,  -74.5544 # CNV4 # hawkesbury WEST
#     target_lat, target_lon = 45.5828,  -74.5489 # CPG5 # hawkesbury EAST
#
#     print("--- Nearest Point ---")
#     nearest, distance = finder.findNearest(target_lat, target_lon, calcDistance=True)
#     print(nearest)
#     print(f"\tdistance: {distance} km")
