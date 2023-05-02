"""
Dumps data stored in the 'pos' buckets during the previous week into a file

Crontab entry:
0 5 * * mon cd /home/ibisek/wqz/prog/python/ognLogbook; ./exportInfluxDataWeekly.sh > /dev/null
"""

from collections import namedtuple
import os
from typing import List

from dateutil import parser
from datetime import datetime, timedelta, timezone

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread

DUMP_FILEPATH_TEMPLATE = '{}/ogn_logbook.{}_{:02}.csv'

# TODO configurable INFLUX_DB_NAME
# TODO configurable DUMP_FILEPATH_TEMPLATE

Interval = namedtuple('Interval', ['startTs', 'endTs'])


def _getTsIntervals10Min(startDt: datetime, endDt: datetime) -> List[Interval]:
    hours = (endDt-startDt).days*24
    minStep = 10   # [min]
    l = []
    for h in range(0, hours):
        for m in range(0, 60, minStep):
            startTs = int((startDt + timedelta(hours=h, minutes=m, seconds=0)).replace(tzinfo=timezone.utc).timestamp())
            endTs = int((startDt + timedelta(hours=h, minutes=m+minStep-1, seconds=59, microseconds=999999)).replace(tzinfo=timezone.utc).timestamp())
            interval = Interval(startTs=startTs, endTs=endTs)
            l.append(interval)

    return l


# def _getTsIntervalsByHour(startDt: datetime, endDt: datetime) -> List[Interval]:
#     hours = (endDt-startDt).days*24
#     l = []
#     for h in range(0, hours):
#         startTs = int((startDt + timedelta(hours=h)).replace(tzinfo=timezone.utc).timestamp())
#         endTs = int((startDt + timedelta(hours=h+1)).replace(tzinfo=timezone.utc).timestamp())
#         interval = Interval(startTs=startTs, endTs=endTs)
#         l.append(interval)
#
#     return l


def _dataFromInflux(influx, interval: Interval):
    a = datetime.fromtimestamp(interval.startTs).strftime("%a %Y-%m-%d %H:%M:%S")
    b = datetime.fromtimestamp(interval.endTs).strftime("%a %Y-%m-%d %H:%M:%S")
    print(f"Retrieving data {a} -> {b}")

    q = f"select * from pos where time >= {interval.startTs}000000000 and time <= {interval.endTs}000000000"
    return influx.client.query(query=q)


def _parseEnvVars():
    influxDbName = os.environ.get('INFLUX_DB_NAME', INFLUX_DB_NAME)
    storageDir = os.environ.get('STORAGE_DIR', '/tmp/00')

    print(f"[INFO] Using\n\tinfluxDbName: {influxDbName}\n\tarchive storageDir: {storageDir}")

    return (influxDbName, storageDir)


if __name__ == '__main__':
    influxDbName, storageDir = _parseEnvVars()

    dt = datetime.utcnow()

    prevMonday = dt + timedelta(days=-dt.weekday() - 7)
    prevSunday = dt + timedelta(days=-dt.weekday())

    monday1 = prevMonday.replace(hour=0, minute=0, second=0, microsecond=0)
    monday2 = prevSunday.replace(hour=0, minute=0, second=0, microsecond=0)

    print("monday1:", monday1)
    print("monday2:", monday2)

    year = monday1.year
    week = monday1.isocalendar()[1]
    outFilePath = DUMP_FILEPATH_TEMPLATE.format(storageDir, year, week)
    print(f"[INFO] Exporting influx data into '{outFilePath}'..")

    # --

    influx = InfluxDbThread(dbName=influxDbName, host=INFLUX_DB_HOST)

    numRecords = 0
    with open(outFilePath, 'w') as f:
        header = 'ts;addr;alt;gs;lat;lon;tr;vs;ss\n'
        f.write(header)

        # tsIntervals = _getTsIntervalsByHour(monday1, monday2)
        tsIntervals = _getTsIntervals10Min(monday1, monday2)
        for interval in tsIntervals:
            rs = _dataFromInflux(influx, interval)

            for r in rs:
                print('Num records in result set:', len(r))
                for res in r:
                    ts = int(parser.parse(res['time']).timestamp()*1000000000)
                    addr = res['addr']
                    alt = res['alt']
                    gs = res['gs']          # ground speed
                    lat = res['lat']
                    lon = res['lon']
                    tr = res['tr']          # turn rate
                    vs = res['vs']          # vertical speed
                    ss = round(res.get('ss', 0))   # signal strength

                    line = f"{ts};{addr};{alt:.1f};{gs:.1f};{lat:.5f};{lon:.5f};{tr};{vs:.2f};{ss}\n"
                    # print(line.strip())
                    f.write(line)

                    numRecords += 1

    influx.client.close()

    print(f"[INFO] Exported {numRecords} lines of data.")

    cmd = f"xz -9e {outFilePath}"
    os.system(cmd)

    print('KOHEU.')
