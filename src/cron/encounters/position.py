from math import radians


class Position:
    def __init__(self, ts: int, addr: str, lat: float, lon: float, alt: float):
        self.ts = ts
        self.addr = addr
        self.lat = lat
        self.lon = lon
        self.alt = alt

        self._lat_rad = None
        self._lon_rad = None

    @property
    def lat_rad(self):
        if not self._lat_rad:
            self._lat_rad = radians(self.lat)

        return self._lat_rad

    @property
    def lon_rad(self):
        if not self._lon_rad:
            self._lon_rad = radians(self.lon)

        return self._lon_rad
