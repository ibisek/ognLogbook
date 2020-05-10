from collections import namedtuple

Event = namedtuple('Event', ['ts', 'address', 'addressType', 'aircraftType', 'event',
                                                 'lat', 'lon', 'location_icao'])


if __name__ == '__main__':

    data: Event = Event(
        ts='ts',
        address='address',
        addressType='addressType',
        aircraftType='aircraftType',
        event='event',
        lat='LAT',
        lon='lon',
        location_icao=None
    )

    print(data)
