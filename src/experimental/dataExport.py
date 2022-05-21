"""
Print out the entire day's data in json-record-per-line format.

Crontab entry:
1 0 0 * * cd /home/ibisek/wqz/prog/python/ognLogbook/ && d=`date -d "yesterday" '+%Y-%m-%d'` && source ./venv/bin/activate && cd src && export PYTHONPATH=. && python experimental/dataExport.py | xz -9e > /opt/zalohy/ognLogbook.$d.dump.xz && deactivate && cd ..

"""

import sys
from datetime import datetime, timedelta

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread

if __name__ == '__main__':

    print(sys.argv)

    if len(sys.argv) == 2:
        dateCandidate = sys.argv[1]
        date = datetime.strptime(dateCandidate, "%Y-%m-%d")

    else:   # in case of no parameter export the previous day
        date = datetime.now()
        date.replace(hour=0, minute=0, second=0, microsecond=0)
        date = date - timedelta(days=1)     # the previous day

    nextDay = date + timedelta(days=1)
    print(f"[INFO] date: {date}; nextDay: {nextDay}")

    query = f"select * from pos where time>={int(date.timestamp())}000000000 and time<{int(nextDay.timestamp())}000000000 order by time;"   # limit 10
    print(f"[INFO] query: {query}")

    influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)
    resultSet = influxDb.query(query)
    for row in list(resultSet.get_points()):
        print(row)
