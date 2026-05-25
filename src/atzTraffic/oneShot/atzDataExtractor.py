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
    # WANTED_GEOHASHES = getGeohashesFor('LKKA')          # ['u2g2v', 'u2g2z', 'u2g2w', 'u2g2t', 'u2g2x', 'u2g3n', 'u2g3j', 'u2g3p', 'u2g2y']
    # WANTED_GEOHASHES.extend(getGeohashesFor('LKMK'))    # ['u2gg6', 'u2ggk', 'u2gg5', 'u2gg4', 'u2ggh', 'u2gge', 'u2ggd', 'u2ggs', 'u2gg7']

    # 9 neighbours:
    # WANTED_GEOHASHES = ['u2g2v', 'u2g2z', 'u2g2w', 'u2g2t', 'u2g2x', 'u2g3n', 'u2g3j', 'u2g3p', 'u2g2y']
    # WANTED_GEOHASHES.extend(['u2gg6', 'u2ggk', 'u2gg5', 'u2gg4', 'u2ggh', 'u2gge', 'u2ggd', 'u2ggs', 'u2gg7'])

    # 25 neighbours:
    WANTED_GEOHASHES = ['u2g3q', 'u2g8b', 'u2g2w', 'u2g2m', 'u2g3n', 'u2g2x', 'u2g2k', 'u2g82', 'u2g2q', 'u2g2u', 'u2g88', 'u2g2r', 'u2g2t', 'u2g3h', 'u2g2z', 'u2g3m', 'u2g2v', 'u2g3j', 'u2g92', 'u2g3k', 'u2g3r', 'u2g3p', 'u2g90', 'u2g2y', 'u2g2s']
    WANTED_GEOHASHES.extend(['u2gg9', 'u2gg7', 'u2gfv', 'u2gg1', 'u2gge', 'u2gfc', 'u2ggc', 'u2gg5', 'u2gfg', 'u2ggs', 'u2ggh', 'u2ggj', 'u2ggt', 'u2ggm', 'u2ggf', 'u2gff', 'u2gg4', 'u2gg3', 'u2ggu', 'u2ggk', 'u2gg6', 'u2ggd', 'u2gfu', 'u2ggg', 'u2ggv'])

    CSV_ROOT = "/media/samba/temp/archiv/2025"
    # CSV_ROOT = "/home/ibisek/btsync/doma/temp"
    # CSV_ROOT = "/home/ibisek/btsync/krizanov/temp"

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

                    if lat == 90.0:
                        continue

                except ValueError:
                    continue

                try:
                    gh = geohash.encode(lat, lon, precision=5)  # 4 ~ 30km, 5 ~ 5km, 6 ~ 1km
                    if gh in WANTED_GEOHASHES:
                        writeF.write(line)
                except Exception as e:
                    print(f"[ERROR] lat: {lat}; lon: {lon} ", e)

    print('KOHEU.')
