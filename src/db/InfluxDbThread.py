"""
Created on Jul 9, 2020

@author: ibisek

Speeds-up DB inserts by not opening and closing cursors after every statement.
"""


import time
import threading
from queue import Empty, Queue
import multiprocessing as mp
from configuration import USE_MULTIPROCESSING_INSTEAD_OF_THREADS

import requests
from influxdb import InfluxDBClient
from influxdb.resultset import ResultSet
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError


class InfluxDbThread(threading.Thread):

    def __init__(self, dbName: str, host: str, port: int = 8086, startThread=True):
        super(InfluxDbThread, self).__init__()

        self.toDoStatements = mp.Manager().Queue() if USE_MULTIPROCESSING_INSTEAD_OF_THREADS else Queue()

        self.dbName = dbName
        self.host = host
        self.port = port

        self._connect()

        if startThread:
            self.doRun = True

    def _connect(self):
        print(f"[INFO] Connecting to influx db '{self.dbName}' at {self.host}:{self.port} ")
        self.client = InfluxDBClient(host=self.host, port=self.port, database=self.dbName)

    def stop(self):
        self.doRun = False
        
    def addStatement(self, sql):
        self.toDoStatements.put(sql)

    def query(self, query) -> ResultSet:
        return self.client.query(query)

    def run(self):
        while self.doRun or self.toDoStatements.qsize() > 0:
            queries = list()
            while self.toDoStatements.qsize() > 0:
                try:
                    query = self.toDoStatements.get(block=False)
                except Empty:  # _queue.Empty (cannot catch it in any other way)
                    break

                if query:
                    # print(f"[INFO] influxDbThread sql: {query}")
                    queries.append(query)

                if len(queries) >= 1000:
                    break   # influx writes are optimised to 5000 queries/batch

            if len(queries) > 0:
                try:
                    res = self.client.write(data=queries, params={'db': self.dbName}, expected_response_code=204, protocol='line')

                except InfluxDBClientError as e:
                    print(f"[ERROR] when executing influx query: '{query}' -> {e}")
                    # for query in queries:
                    #     self.toDoStatements.put(query)  # requeue for retry

                except (requests.exceptions.ConnectionError, InfluxDBServerError) as e:
                    print(f"[ERROR] when connecting to influx db at {self.host}:{self.port}", str(e))
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

