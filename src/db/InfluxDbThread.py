"""
Created on Jul 9, 2020

@author: ibisek

Speeds-up DB inserts by not opening and closing cursors after every statement.
"""


import sys
import time
import threading

import requests
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError


class InfluxDbThread(threading.Thread):

    def __init__(self, dbName: str, host: str, port: int = 8086):
        super(InfluxDbThread, self).__init__()

        self.dbName = dbName
        self.host = host
        self.port = port

        self._connect()

        self.toDoStatements = []
        self.toDoStatementsLock = threading.Lock()
        
        self.doRun = True

    def _connect(self):
        print(f"[INFO] Connecting to influx db '{self.dbName}' at {self.host}:{self.port} ")
        self.client = InfluxDBClient(host=self.host, port=self.port, database=self.dbName)

    def stop(self):
        self.doRun = False
        
    def addStatement(self, sql):
        with self.toDoStatementsLock:
            self.toDoStatements.append(sql)
            
    def run(self):
        while self.doRun or len(self.toDoStatements) > 0:

            if len(self.toDoStatements) > 0:
                with self.toDoStatementsLock:
                    while len(self.toDoStatements) > 0:
                        query = self.toDoStatements.pop()
                        # print(f"[INFO] influxDbThread sql: {query}")

                        try:
                            res = self.client.write(data=query, params={'db': self.dbName}, expected_response_code=204, protocol='line')

                        except InfluxDBClientError as e:
                            print(f"[ERROR] when executing influx query: '{query}' -> {e}")
                            self.toDoStatements.append(query)  # requeue for retry

                        except requests.exceptions.ConnectionError as e:
                            print(f"[ERROR] when connecting to influx db at {self.host}:{self.port}")
                            raise e

            else:
                time.sleep(1)

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

