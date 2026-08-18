"""
More sophisticated geo-distace finder than the original one ;)
"""

from math import radians

import numpy as np
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
        """
        Initializes the spatial tree using a list of dicts.
        """
        self.records = records

        # Extract lat/lon arrays for fast vectorization
        lats = np.array([record.lat for record in records])
        lons = np.array([record.lon for record in records])
        alts = [record.alt for record in records]

        # Convert dataset to 3D Cartesian points (in meters)
        self.points_3d = recordToCartesian3d(lats, lons, alts)
        self.tree = KDTree(self.points_3d)

    def findNearest(self, lat: float, lon: float, alt: float = 0.0, units: Units = Units.DEG, calcDistance=False):
        """
        Finds the nearest record in the dataset for a given query point.
        :lat in degrees
        :lon in degrees
        :alt im meters
        """

        if units is Units.DEG:
            lat_rad = radians(lat)
            lon_rad = radians(lon)
        else:
            lat_rad = lat
            lon_rad = lon

        query3d = recordToCartesian3d(lat_rad, lon_rad, float(alt))

        _, nearest_idx = self.tree.query(query3d)

        # Calculate true surface ground distance (Haversine) for exact precision
        matchedRecord = self.records[nearest_idx]

        distanceKm = None
        if calcDistance:
            distanceKm = self._haversineKm(lat_rad, lon_rad, matchedRecord.lat, matchedRecord.lon)

        return matchedRecord, distanceKm

    @staticmethod
    def _haversineKm(lat1, lon1, lat2, lon2):
        """
        Exact great-circle distance on Earth surface in kilometers.
        :param lat1 in radians
        :param lon1 in radians
        :param lat2 in radians
        :param lon2 in radians
        """

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2)

        a_clipped = np.clip(a, 0.0, 1.0)    # Protect against floating-point inaccuracy resulting in a > 1.0

        return float(round(6371.0 * 2.0 * np.arcsin(np.sqrt(a_clipped)), 3))    # np.float -> float


# if __name__ == '__main__':
#     airfields, _ = AirfieldManager.loadAirfieldsFromFile()
#
#     finder = NearestGeoPointFinder(records=airfields)
#
#     # target_lat, target_lon = 45.4861, -75.0961  # CNF3
#     target_lat, target_lon = 45.5833,  -74.5544 # CNV4
#
#     print("--- Nearest Point ---")
#     nearest, distance = finder.findNearest(target_lat, target_lon, calcDistance=True)
#     print(nearest)
#     print(f"\tdistance: {distance} km")
