#
# A script to merge list of already know airfields with
# OPENAIP location information file.
#

import os
import json

AIRFIELDS_FN = '../../data/airfields.json'
AIRFIELDS_FN_new = '../../data/airfields.json.new'

AIRFIELDS_FN_OPENAIP = '../../data/airfields-openAip.json'

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
            alt = int(item.get('alt', 0))
            airfields[code] = {'lat': lat, 'lon': lon, 'alt': alt}

    nAccepted = 0
    nModified = 0
    nRejected = 0
    with open(AIRFIELDS_FN_OPENAIP, 'r') as f:
        while line := f.readline().strip():
            l = json.loads(line)

            code = item.get('code', None)
            lat = float(item.get('lat', 0))
            lon = float(item.get('lon', 0))
            alt = int(item.get('alt', 0))

            lat = float(f'{lat: .4f}')
            lon = float(f'{lon: .4f}')

            af = airfields.get(code, None)
            if not af:
                airfields[code] = {'lat': lat, 'lon': lon, 'alt': alt}
                nAccepted += 1
            else:
                x = af.get('alt')
                if not x:
                    af['alt'] = alt
                    nModified += 1
                else:
                    nRejected += 1

    print('Total num of airfield locations:', len(airfields))
    print(f"  nAccepted: {nAccepted}\n  nModified: {nModified}\n  nRejected: {nRejected}")

    if nAccepted > 0 or nModified > 0:
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
