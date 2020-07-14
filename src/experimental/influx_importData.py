
import time

from configuration import INFLUX_DB_NAME, INFLUX_DB_HOST
from db.InfluxDbThread import InfluxDbThread

from experimental.influx_exportData import DUMP_FILEPATH

if __name__ == '__main__':

    influx = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)
    influx.start()

    with open(DUMP_FILEPATH, 'r') as f:
        line = f.readline()
        print(line)
        influx.addStatement(line)

    while influx.toDoStatements.qsize() > 0:
        time.sleep(1)  # ~ thread.yield()

    print('KOHEU.')
