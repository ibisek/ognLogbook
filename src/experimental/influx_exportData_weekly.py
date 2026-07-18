"""
Dumps data stored in the 'pos' buckets during the previous week into a file

Crontab entry:
0 1 * * tue cd /home/ibisek/wqz/prog/python/ognLogbook && export INFLUX_DB_NAME='ogn_logbook_ps' && ./scripts/exportInfluxDataWeekly.sh > /dev/null
0 3 * * tue cd /home/ibisek/wqz/prog/python/ognLogbook && export INFLUX_DB_NAME='ogn_logbook' && ./scripts/exportInfluxDataWeekly.sh > /dev/null

for i in {14..15}; do echo "WEEK: $i" && export INFLUX_DB_NAME='ogn_logbook_ps' && export WEEK_NUMBER=$i && ./scripts/exportInfluxDataWeekly.sh; done
"""

from collections import namedtuple
import os
from time import sleep
from typing import List

from dateutil import parser
from datetime import datetime, timedelta, timezone

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread

DUMP_FILEPATH_TEMPLATE = '{}/{}.{}_{:02}.csv'   # storageDir, db_name, year, week

Interval = namedtuple('Interval', ['startTs', 'endTs'])


def _getTsIntervalsXMin(startDt: datetime, endDt: datetime, stepMin: int = 5) -> List[Interval]:
    hours = (endDt-startDt).days*24
    l = []
    for h in range(0, hours):
        for m in range(0, 60, stepMin):
            startTs = int((startDt + timedelta(hours=h, minutes=m, seconds=0)).replace(tzinfo=timezone.utc).timestamp())
            endTs = int((startDt + timedelta(hours=h, minutes=m+stepMin-1, seconds=59, microseconds=999999)).replace(tzinfo=timezone.utc).timestamp())
            interval = Interval(startTs=startTs, endTs=endTs)
            l.append(interval)

    return l


def _dataFromInflux(influx, interval: Interval):
    a = datetime.fromtimestamp(timestamp=interval.startTs, tz=timezone.utc).strftime("%a %Y-%m-%d %H:%M:%S")
    b = datetime.fromtimestamp(timestamp=interval.endTs, tz=timezone.utc).strftime("%a %Y-%m-%d %H:%M:%S")
    print(f"Retrieving data {a} -> {b}")

    q = f"select * from pos where time >= {interval.startTs}000000000 and time <= {interval.endTs}000000000"
    return influx.client.query(query=q)


def _parseEnvVars():
    influxDbName = os.environ.get('INFLUX_DB_NAME', INFLUX_DB_NAME)
    storageDir = os.environ.get('STORAGE_DIR', '/tmp/00')
    weekNumber = os.environ.get('WEEK_NUMBER', None)

    print(f"[INFO] Using\n\tinfluxDbName: {influxDbName}\n\tarchive storageDir: {storageDir}\n\tweek number: {weekNumber}")

    return influxDbName, storageDir, weekNumber


if __name__ == '__main__':
    influxDbName, storageDir, weekNumber = _parseEnvVars()

    dt = datetime.now(tz=timezone.utc)

    if weekNumber:  # this is an override to export a specific week
        d = f"{dt.year}-W{weekNumber}"
        dt = datetime.strptime(d + '-1', "%Y-W%W-%w").replace(tzinfo=timezone.utc)
        monday1 = dt                         # monday of the specified week
        monday2 = dt + timedelta(days=7)     # monday of the specified week+1

    else:
        prevMonday = dt + timedelta(days=-dt.weekday() - 7)
        prevSunday = dt + timedelta(days=-dt.weekday())

        monday1 = prevMonday.replace(hour=0, minute=0, second=0, microsecond=0)
        monday2 = prevSunday.replace(hour=0, minute=0, second=0, microsecond=0)

        weekNumber = monday1.isocalendar()[1]

    print("monday1:", monday1)
    print("monday2:", monday2)

    year = monday1.year
    outFilePath = DUMP_FILEPATH_TEMPLATE.format(storageDir, influxDbName, year, weekNumber)
    print(f"[INFO] Exporting influx data into '{outFilePath}'..")

    # If file already exists seek to the end and retrieve last inserted timestamp to continue data export from this ts:
    resume = False
    if os.path.exists(outFilePath):
        with open(outFilePath, 'r') as f:    # fetch last line of the file
            lastLine = f.readlines()[-1]

        ts = int(lastLine.split(';')[0].replace('000000000', ''))
        monday1 = datetime.fromtimestamp(int(ts), tz=timezone.utc)  # not essentially a monday ;P

        resume = True
        print(f"resuming data export from {str(monday1)} (ts {ts})")

    # --

    influx = InfluxDbThread(dbName=influxDbName, host=INFLUX_DB_HOST)

    writeMode = 'a' if resume else 'w'
    numRecords = 0
    with open(outFilePath, writeMode) as f:
        if not resume:
            header = 'ts;addr;alt;gs;lat;lon;tr;vs;ss\n'
            f.write(header)

        tsIntervals = _getTsIntervalsXMin(startDt=monday1, endDt=monday2, stepMin=5)
        for interval in tsIntervals:
            dataRetrieved = False
            while not dataRetrieved:
                try:
                    rs = _dataFromInflux(influx, interval)
                    dataRetrieved = True
                except Exception as ex: # InvalidChunkLength - something is broken in the DB
                    print(f"[ERROR] when retrieving data from influx:", str(ex))
                    sleep(60)   # give influx some rest

            for r in rs:
                print('Num records in result set:', len(r))
                for res in r:
                    ts = int(parser.parse(res['time']).timestamp())
                    addr = res['addr']
                    alt = res['alt']
                    gs = res['gs']          # ground speed
                    lat = res['lat']
                    lon = res['lon']
                    tr = res['tr']          # turn rate
                    vs = res['vs']          # vertical speed
                    ss = round(res.get('ss', 0) or 0)   # signal strength

                    line = f"{ts};{addr};{alt:.1f};{gs:.1f};{lat:.5f};{lon:.5f};{tr};{vs:.2f};{ss}\n"
                    # print(line.strip())
                    f.write(line)

                    numRecords += 1

    influx.client.close()

    print(f"[INFO] Exported {numRecords} lines of data.")

    # cmd = f"sed -i 's/000000000//g' {outFilePath}"
    # os.system(cmd)

    # cmd = f"xz -9e {outFilePath}"
    cmd = f"zpaq a {outFilePath}.zpaq {outFilePath} -m5 -t4"
    os.system(cmd)

    print('KOHEU.')
