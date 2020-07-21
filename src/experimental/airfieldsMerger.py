
import json

AIRFIELDS_FN = '../../data/airfields.json'
AIRFIELDS_FN_new = '../../data/airfields.json.new'

# OSM = '/home/jaja/btsync/doma/ogn/00-letiste/airfields-europe.csv'
OSM = '/home/jaja/btsync/doma/ogn/00-letiste/airfields-africa.csv'
# OSM = '/home/jaja/btsync/doma/ogn/00-letiste/airfields-oceania.csv'
# OSM = '/home/jaja/btsync/doma/ogn/00-letiste/airfields-camerica.csv'
# OSM = '/home/jaja/btsync/doma/ogn/00-letiste/airfields-namerica.csv'
# OSM = '/home/jaja/btsync/doma/ogn/00-letiste/airfields-samerica.csv'

if __name__ == '__main__':

    afs = dict()
    with open(AIRFIELDS_FN, 'r') as f:
        l = json.load(f)
        for item in l:
            code = item.get('code', None)
            lat = float(item.get('lat', 0))
            lon = float(item.get('lon', 0))
            afs[code] = {'lat': lat, 'lon': lon}

    new = 0
    old = 0
    with open(OSM, 'r') as f:
        for line in f:
            (code, lat, lon) = line.strip().split(';')
            lat = float(lat)
            lon = float(lon)

            if code not in afs and len(code) == 4:
                afs[code] = {'lat': lat, 'lon': lon}
                new += 1
            else:
                # print(f'{code} already in list')
                old += 1

    print(f'New: {new}, old: {old}')

    with open(AIRFIELDS_FN_new, 'w') as f:
        j = json.dumps(afs)
        f.write(j)

    print('KOHEU.')
