
from datetime import datetime

from utils import formatDuration


class Status(object):

    def __init__(self, s=-1, ts=0):
        """
        :param s: 0 = on ground, 1 = airborne, -1 = unknown
        :param ts: [s]
        """
        self.s = int(s)
        self.ts = int(ts)

    def __str__(self):
        return f"{self.s};{self.ts}"

    @staticmethod
    def parse(s):
        items = s.split(';')

        if len(items) != 2:
            raise ValueError(s)

        s: Status = Status(s=items[0], ts=int(items[1]))

        return s


class LogbookItem(object):

    def __init__(self, id, address, address_type=None,
                 takeoff_ts=0, takeoff_lat=0, takeoff_lon=0, takeoff_icao=None,
                 landing_ts=0, landing_lat=0, landing_lon=0, landing_icao=None,
                 flight_time=0, flown_distance=0, in_ps=False,
                 device_type=None,
                 registration=None, cn=None, aircraft_type=None, tow_id=None):

        self.id = id
        self.address = address
        self.address_type = address_type

        self.takeoff_ts = takeoff_ts
        self.takeoff_lat = takeoff_lat
        self.takeoff_lon = takeoff_lon
        self.takeoff_icao = takeoff_icao

        self.landing_ts = landing_ts
        self.landing_lat = landing_lat
        self.landing_lon = landing_lon
        self.landing_icao = landing_icao

        self.flight_time = flight_time
        self.flown_distance = flown_distance
        self.in_ps = in_ps

        self.device_type = device_type

        self.registration = registration
        self.cn = cn
        self.aircraft_type = aircraft_type

        self.takeoff_dt = datetime.fromtimestamp(takeoff_ts) if self.takeoff_ts else None
        self.landing_dt = datetime.fromtimestamp(landing_ts) if self.landing_ts else None

        self.flight_time = formatDuration(self.flight_time)

        self.tow_id = tow_id


addressPrefixes = {'O': 'OGN', 'I': 'ICA', 'F': 'FLR', 'S': 'SKY'}
