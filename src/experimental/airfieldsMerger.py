#
# A script to merge list of already know airfields with
# OSM-extracted location information CSV files.
#

import os
import json

AIRFIELDS_FN = '../../data/airfields.json'
AIRFIELDS_FN_new = '../../data/airfields.json.new'

OSM_ROOT_DIR = '/home/jaja/btsync/doma/ogn/00-letiste/'

new = 0
old = 0


def addToAfs(filepath, afs):
    new = 0
    old = 0

    print(f'[INFO] Reading {filepath}')
    with open(filepath, 'r') as f:
        for line in f:
            items = line.strip().split(';')

            code = None
            lat = 0
            lon = 0

            if len(items) == 3:
                (code, lat, lon) = items
            elif len(items) == 4:   # australian speciality
                (code, code2, lat, lon) = items

            lat = float(lat)
            lon = float(lon)

            if (code not in afs) and (4 <= len(code) <= 6):
                afs[code] = {'lat': lat, 'lon': lon}
                new += 1
            else:
                # print(f'{code} already in list')
                old += 1

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

    files = os.listdir(OSM_ROOT_DIR)
    for filename in files:
        if filename.endswith('.csv'):
            filepath = f"{OSM_ROOT_DIR}/{filename}"
            addToAfs(filepath, afs)

    with open(AIRFIELDS_FN_new, 'w') as f:
        l = list()
        for key in afs.keys():
            af = afs[key]
            lat = af['lat']
            lon = af['lon']

            d = dict()
            d['code'] = key
            d['lat'] = lat
            d['lon'] = lon

            l.append(d)

        # sort the list by latitude:
        l.sort(key=lambda x: x['lat'])

        j = json.dumps(l)
        f.write(j)

    print('KOHEU.')
