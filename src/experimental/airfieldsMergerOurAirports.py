#
# A script to merge list of already know airfields with
# https://ourairports.com/
#
# https://ourairports.com/countries/GB/airports.hxl
#

import os
import json

AIRFIELDS_FN = '../../data/airfields.json'
AIRFIELDS_FN_new = '../../data/airfields.json.new'

AIRFIELDS_FN_INCOMING = '../../data/se-airports.csv'

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

    print('Total (old) num of airfield locations:', len(airfields))

    nAccepted = 0
    nRejected = 0
    with open(AIRFIELDS_FN_INCOMING, 'r') as f:
        lines = f.readlines()
        for line in lines:
            items = line.split(',')

            try:
                code = items[1]
                if code == 'GB-0429':
                    print(666)

                int(items[0])  # this is just to detect valid entries; id shall be numeric
                code = items[1]
                type = items[2]
                lat = float(items[4])
                lon = float(items[5])

                # some strips are without elevation
                if items[6]:
                    eleFt = float(items[6])
                else:
                    eleFt = 0

                lat = float(f'{lat:.4f}')
                lon = float(f'{lon:.4f}')
                alt = round(eleFt * 0.3048) # [ft] -> [m]

            except ValueError as e:
                continue

            if type.lower() in ['closed', 'heliport']:
                nRejected += 1
                continue    # ignore closed strips

            # print(code, lat, lon, alt)

            if code not in airfields:
                airfields[code] = {'lat': lat, 'lon': lon}
                if alt:
                    airfields[code]['alt'] = alt

                nAccepted += 1
            else:
                entry = airfields[code]
                if alt and 'alt' not in entry:
                    airfields[code]['alt'] = alt
                else:
                    nRejected += 1

    print('Total (new) num of airfield locations:', len(airfields))
    print(f"  nAccepted: {nAccepted}\n  nRejected: {nRejected}")

    with open(AIRFIELDS_FN_new, 'w') as f:
        l = list()
        for key in airfields.keys():
            af = airfields[key]
            lat = af['lat']
            lon = af['lon']
            alt = af.get('alt', None)

            d = dict()
            d['code'] = key
            d['lat'] = lat
            d['lon'] = lon
            if alt:
                d['alt'] = alt

            l.append(d)

        # sort the list by latitude:
        l.sort(key=lambda x: x['lat'])

        j = json.dumps(l)
        f.write(j)

    print('KOHEU.')
