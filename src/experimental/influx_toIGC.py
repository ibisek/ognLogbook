#
# A script to generate .IGC file for specified ADDR and given DATE.
#

from datetime import datetime

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread
from igc import flightToIGC


if __name__ == '__main__':

    influx = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)

    # 2023-09-14 LKTO
    # ADDR = 'FLRDDC39C'
    # ADDR = 'OGN2ACE1F'
    # ADDR = 'ICA3DB46A'
    # ADDR = 'ICA3EC931'
    # ADDR = 'ICA4B080B'
    ADDR = 'ICA49C262'

    startDate = '2023-09-14'

    dt: datetime = datetime.strptime(startDate, '%Y-%m-%d')
    ts = dt.timestamp()     # [s]
    startTs = f"{ts:.0f}000000000"

    query = f"select * from pos where addr='{ADDR}' and time > {startTs}"

    influxDb = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST, startThread=False)
    flightRecord = []
    rs = influxDb.client.query(query=query)
    if not rs:
        print('No data.');

    else:
        for row in rs.get_points():
            try:
                row['dt'] = datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                row['dt'] = datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            flightRecord.append(row)

        igc = flightToIGC(flightRecord)

        filepath = f"/tmp/00/{startDate}_{ADDR}.igc"
        print('Writing to', filepath)
        with open(filepath, 'w') as f:
            f.write(igc)

    print('KOHEU.')
