#
# A script to merge list of already know airfields with
# Wikipedia-extracted location information file.
#

import os
import json

AIRFIELDS_FN = '../../data/airfields.json'
AIRFIELDS_FN_new = '../../data/airfields.json.new'

AIRFIELDS_FN_WIKI = '../../data/airfields-wikipedia.json'

new = 0
old = 0

if __name__ == '__main__':

    airfields = dict()

    with open(AIRFIELDS_FN, 'r') as f:
        l = json.load(f)
        for item in l:
            code = item.get('code', None)
            lat = float(item.get('lat', 0))
            lon = float(item.get('lon', 0))
            airfields[code] = {'lat': lat, 'lon': lon}

    with open(AIRFIELDS_FN_WIKI, 'r') as f:
        l = json.load(f)
        for item in l:
            code = item.get('code', None)
            lat = float(item.get('lat', 0))
            lon = float(item.get('lon', 0))

            lat = float(f'{lat:.4f}')
            lon = float(f'{lon:.4f}')

            if code not in airfields:
                airfields[code] = {'lat': lat, 'lon': lon}

    print('Total num of airfield locations:', len(airfields))

    with open(AIRFIELDS_FN_new, 'w') as f:
        l = list()
        for key in airfields.keys():
            af = airfields[key]
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
