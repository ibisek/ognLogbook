"""
Created on Jul 9, 2020

@author: ibisek

Speeds-up DB inserts by not opening and closing cursors after every statement.
"""


import time
import threading
from queue import Queue, Empty

import requests
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError


class InfluxDbThread(threading.Thread):

    toDoStatements = Queue()

    def __init__(self, dbName: str, host: str, port: int = 8086):
        super(InfluxDbThread, self).__init__()

        self.dbName = dbName
        self.host = host
        self.port = port

        self._connect()

        self.doRun = True

    def _connect(self):
        print(f"[INFO] Connecting to influx db '{self.dbName}' at {self.host}:{self.port} ")
        self.client = InfluxDBClient(host=self.host, port=self.port, database=self.dbName)

    def stop(self):
        self.doRun = False
        
    def addStatement(self, sql):
        self.toDoStatements.put(sql)

    def run(self):
        while self.doRun or self.toDoStatements.qsize() > 0:
            queries = list()
            while self.toDoStatements.qsize() > 0:
                query = self.toDoStatements.get(block=False)
                if query:
                    # print(f"[INFO] influxDbThread sql: {query}")
                    queries.append(query)

                if len(queries) >= 5000:
                    break   # influx is said to be optimised to 5000 queries/batch

            if len(queries) > 0:
                try:
                    res = self.client.write(data=queries, params={'db': self.dbName}, expected_response_code=204, protocol='line')

                except InfluxDBClientError as e:
                    print(f"[ERROR] when executing influx query: '{query}' -> {e}")
                    # for query in queries:
                    #     self.toDoStatements.put(query)  # requeue for retry

                except (requests.exceptions.ConnectionError, InfluxDBServerError) as e:
                    print(f"[ERROR] when connecting to influx db at {self.host}:{self.port}")
                    self._connect()

            if len(queries) < 1000:     # ~ wait for more items in the queue to save network resources a bit..
                time.sleep(1)  # ~ thread.yield()

        if self.client:
            self.client.close()

        print("InfluxDbThread terminated")


if __name__ == '__main__':
    INFLUX_DB_NAME = 'ognLogbook'
    INFLUX_DB_HOST = '127.0.0.1'

    db = InfluxDbThread(dbName=INFLUX_DB_NAME, host=INFLUX_DB_HOST)
    db.start()

    ts = int(time.time())
    db.addStatement(f"positions,addr=123456 lat=111,lon=222,alt=333,gs=444,agl=0,vs=0,tr=0 {ts}000000000")

    time.sleep(4)
    db.stop()
    time.sleep(4)

    print('KOHEU.')

