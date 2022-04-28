
from dateutil import parser

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread

DUMP_FILEPATH = '/tmp/00/ogn_logbook.dump'
# DUMP_FILEPATH = '/tmp/00/ogn_logbook-2022-04-26.dump'

if __name__ == '__main__':

    influx = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)

    # measurements = influx.client.get_list_measurements()
    series = influx.client.get_list_series(database=INFLUX_DB_NAME)

    with open(DUMP_FILEPATH, 'w') as f:
        for serie in series:
            (name, tags) = serie.split(',')
            (tagName, value) = tags.split('=')

            q = f"select * from {name} where {tagName}='{value}'"
            # q = f"select * from {name} where {tagName}='{value}' and time > 1650924000000000000 and time < 1651010400000000000"  # 26.04.2022
            rs = influx.client.query(query=q)
            for r in rs:
                # print('Num records in result set:', len(r))
                for res in r:
                    ts = int(parser.parse(res['time']).timestamp())
                    addr = res['addr']
                    alt = res['alt']
                    gs = res['gs']
                    lat = res['lat']
                    lon = res['lon']
                    tr = res['tr']
                    vs = res['vs']

                    insert = f"pos,addr={addr} alt={alt},gs={gs},lat={lat},lon={lon},tr={tr},vs={vs} {ts}000000000"
                    print(insert)

                    f.write(insert)
                    f.write('\n')

    influx.client.close()

    print('KOHEU.')
