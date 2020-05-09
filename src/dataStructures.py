from collections import namedtuple

ProcessedBeacon = namedtuple('ProcessedBeacon', ['ts', 'address', 'addressType', 'aircraftType', 'event', 'lat', 'lon', 'location_icao'])


if __name__ == '__main__':

    data: ProcessedBeacon = ProcessedBeacon(
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




