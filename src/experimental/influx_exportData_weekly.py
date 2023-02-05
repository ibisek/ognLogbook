"""
Dumps data stored in the 'pos' buckets during the previous week into a file

Crontab entry:
0 5 * * 0 cd /home/ibisek/wqz/prog/python/ognLogbook; ./exportInfluxDataWeekly.sh > /dev/null
"""

import os
from dateutil import parser
from datetime import datetime, timedelta, timezone

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread

DUMP_FILEPATH_TEMPLATE = '/tmp/00/ogn_logbook.{}_{:02}.csv'

# TODO configurable INFLUX_DB_NAME
# TODO configurable DUMP_FILEPATH_TEMPLATE

if __name__ == '__main__':

    dt = datetime.utcnow()

    prevMonday = dt + timedelta(days=-dt.weekday() - 7)
    prevSunday = dt + timedelta(days=-dt.weekday() - 1)

    prevMonday = prevMonday.replace(hour=0, minute=0, second=0, microsecond=0)
    prevSunday = prevSunday.replace(hour=23, minute=59, second=59, microsecond=999999)

    # get UTC timestamps:
    startTs = int(prevMonday.replace(tzinfo=timezone.utc).timestamp())
    endTs = int(prevSunday.replace(tzinfo=timezone.utc).timestamp())

    year = prevMonday.year
    week = prevMonday.isocalendar()[1]
    outFilePath = DUMP_FILEPATH_TEMPLATE.format(year, week)
    print(f"[INFO] Exporting influx data into '{outFilePath}'..")

    # --

    influx = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)

    numRecords = 0
    with open(outFilePath, 'w') as f:
        header = 'ts;addr;alt;gs;lat;lon;tr;vs\n'
        f.write(header)

        q = f"select * from pos where time >= {startTs}000000000 and time <= {endTs}000000000"
        rs = influx.client.query(query=q)
        for r in rs:
            # print('Num records in result set:', len(r))
            for res in r:
                ts = int(parser.parse(res['time']).timestamp()*1000000000)
                addr = res['addr']
                alt = res['alt']
                gs = res['gs']
                lat = res['lat']
                lon = res['lon']
                tr = res['tr']
                vs = res['vs']

                line = f"{ts};{addr};{alt:.1f};{gs:.1f};{lat:.5f};{lon:.5f};{tr};{vs:.2f}\n"
                # print(line.strip())
                f.write(line)

                numRecords += 1

    influx.client.close()

    print(f"[INFO] Exported {numRecords} lines of data.")

    cmd = f"xz -9e {outFilePath}"
    os.system(cmd)

    print('KOHEU.')
