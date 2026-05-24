
from os import listdir
from os.path import isfile, join
from time import sleep

import geohash

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread

if __name__ == '__main__':

    # influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST, startThread=False)
    influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)
    influxDb.start()

    CSV_ROOT = "/home/ibisek/btsync/prac/temp/logbook"

    files = [f for f in listdir(CSV_ROOT) if isfile(join(CSV_ROOT, f)) and f.endswith('.csv')]
    files.sort()

    for file in files:
        readFn = join(CSV_ROOT, file)
        print(f"Processing: {readFn}\n")

        with open(readFn, 'r') as f:
            for line in f:
                items = line.strip().split(';')

                try:
                    # ts;addr;alt;gs;lat;lon;tr;vs;ss
                    ts = int(items[0])
                    addr = items[1]
                    alt = float(items[2])
                    gs = float(items[3])
                    lat = float(items[4])
                    lon = float(items[5])
                    tr = float(items[6])
                    vs = float(items[7])
                    ss = float(items[8])

                    if lat == 90.0:
                        continue

                    gh = geohash.encode(lat, lon, precision=5)  # 4 ~ 30km, 5 ~ 5km, 6 ~ 1km
                    aglStr = '0'

                    # TODO
                    q = f"pos,addr={addr},gh={gh} lat={lat:.6f},lon={lon:.6f},alt={alt:.0f},gs={gs:.2f},vs={vs:.2f},tr={tr:.2f},agl={aglStr},ss={ss} {ts}000000000"
                    print("q:", q)
                    # rs = influxDb.client.query(query=q)
                    influxDb.addStatement(q)

                except Exception as e:
                    print('[ERROR] when parsing line items:', e)
                    continue

            while influxDb.toDoStatements.qsize() > 0:
                sleep(5)

    influxDb.stop()
    print("KOHEU.")
