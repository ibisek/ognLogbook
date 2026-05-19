"""
Used for pre-sorting data from the archive files
to retain beacons near the wanted airfield(s) only.
"""
from os import listdir
from os.path import isfile, join

import geohash

from airfieldTrafficDensity import coordsForAirfield


def getGeohashesFor(airfieldCode: str) -> []:
    lat, lon = coordsForAirfield(airfieldCode)
    gh = geohash.encode(lat, lon, precision=5)  # 4 ~ 30km, 5 ~ 5km, 6 ~ 1km
    neighbours = geohash.expand(gh)

    return neighbours   # contains also the midpoint-geohash


if __name__ == '__main__':
    WANTED_GEOHASHES = getGeohashesFor('LKKA')
    WANTED_GEOHASHES.extend(getGeohashesFor('LKMK'))

    # CSV_ROOT = "/mnt/samba/temp/archive"
    CSV_ROOT = "/home/jaja/btsync/doma/temp"

    files = [f for f in listdir(CSV_ROOT) if isfile(join(CSV_ROOT, f)) and f.endswith('.csv')]
    files.sort()

    for file in files:
        readFn = join(CSV_ROOT, file)
        writeFn = join(CSV_ROOT, '_' + file)
        print(f"Processing: {readFn}\n\toutput to: {writeFn}")

        with open(readFn, 'r') as readF, open(writeFn, 'w') as writeF:
            for line in readF:
                # ts;addr;alt;gs;lat;lon;tr;vs;ss\n'
                items = line.rstrip().split(';')
                try:
                    lat = float(items[4])
                    lon = float(items[5])
                except ValueError:
                    continue

                gh = geohash.encode(lat, lon, precision=5)  # 4 ~ 30km, 5 ~ 5km, 6 ~ 1km
                if gh in WANTED_GEOHASHES:
                    writeF.write(line)

    print('KOHEU.')
