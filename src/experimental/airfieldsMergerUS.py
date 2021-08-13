#
# A script to merge list of already know airfields with
# a list of US airfields
# @see http://soaringdata.info/airports/waypoints.php
#

import os
import re
import json

AIRFIELDS_FN = '../../data/airfields.json'
AIRFIELDS_FN_new = '../../data/airfields.json.new'

US_FN = '/tmp/00/airports.cup'

new = 0
old = 0


def addToAfs(afs):
    new = 0
    old = 0

    regex = re.compile('.+?,(\d+[.]\d+N),(\d+[.]\d+W),.+?[(](.+?)[)]')

    with open(US_FN, 'r', encoding='cp1250') as f:
        allLines = f.readlines()
        for line in allLines:
            # ['name', 'code', 'country', 'lat', 'lon', 'elev', 'style', 'rwdir', 'rwlen', 'freq', 'desc']
            try:
                res = regex.search(line)
                if res:
                    lat = res[1]
                    lon = res[2]
                    code = res[3]

                    # '1812.288N', '06303.231W' -> 18.2048000N, 63.0538500W
                    letter = lat[-1]
                    lat = int(lat[:2]) + float(lat[2:-1])/60
                    if letter == 'S':
                        lat = -1 * lat

                    letter = lon[-1]
                    lon = int(lon[:3]) + float(lon[3:-1]) / 60
                    if letter == 'W':
                        lon = -1 * lon

                    if (code not in afs) and (3 <= len(code) <= 6):
                        afs[code] = {'lat': lat, 'lon': lon, 'country': 'US'}
                        new += 1
                    else:
                        print(f'{code} already in list')
                        old += 1

            except ValueError as e:
                continue

        print(f'[INFO] New: {new}, old: {old}')


if __name__ == '__main__':

    afs = dict()

    with open(AIRFIELDS_FN, 'r') as f:
        l = json.load(f)
        for item in l:
            code = item.get('code', None)
            lat = float(item.get('lat', 0))
            lon = float(item.get('lon', 0))
            afs[code] = {'lat': lat, 'lon': lon}

    addToAfs(afs)

    with open(AIRFIELDS_FN_new, 'w') as f:
        l = list()
        for key in afs.keys():
            af = afs[key]
            lat = af['lat']
            lon = af['lon']
            country = af.get('country', None)

            d = dict()
            d['code'] = key
            d['lat'] = lat
            d['lon'] = lon
            if country:
                d['country'] = country

            l.append(d)

        # sort the list by latitude:
        l.sort(key=lambda x: x['lat'])

        j = json.dumps(l)
        f.write(j)

    print('KOHEU.')
