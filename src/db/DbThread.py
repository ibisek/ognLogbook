"""
Created on Feb 5, 2015

@author: ibisek

Speeds-up DB inserts by not opening and closing cursors after every statement.
"""


import sys
import time
import threading
import pymysql
import sqlite3
import multiprocessing as mp

from db.DbSource import DbSource


class DbThread(threading.Thread):

    """
    @param dbConnectionInfo (optional) tuple of (host, port, dbName, dbUser, dbPassword)
    """
    def __init__(self, dbConnectionInfo: dict = None):
        super(DbThread, self).__init__()

        self.dbConnectionInfo = dbConnectionInfo
        
        # self.toDoStatements = []
        self.toDoStatements = mp.Manager().Queue()
        self.toDoStatementsLock = threading.Lock()
        
        self.doRun = True

    def stop(self):
        self.doRun = False
        
    def addStatement(self, sql):
        with self.toDoStatementsLock:
            # self.toDoStatements.append(sql)
            self.toDoStatements.put(sql)

    def run(self):
        numEmptyLoops = 0
        connection = DbSource(self.dbConnectionInfo).getConnection()

        while self.doRun or len(self.toDoStatements) > 0:
            # if len(self.toDoStatements) > 0:
            if not self.toDoStatements.empty():
                numEmptyLoops = 0

                with self.toDoStatementsLock:
                    sql = None
                    try:
                        cur = connection.cursor()
                        # while len(self.toDoStatements) > 0:
                        while self.toDoStatements.qsize() > 0:
                            # sql = self.toDoStatements.pop()
                            sql = self.toDoStatements.get()
                            # print(f"[INFO] dbThread sql: {sql}")
                            try:
                                cur.execute(sql)
                                connection.commit()

                            except (sqlite3.OperationalError, pymysql.err.OperationalError) as ex:
                                sys.stderr.write("error in statement: %s\n" % sql)
                                sys.stderr.write(str(type(ex)) + "\n")
                                sys.stderr.write(str(ex) + "\n")

                        cur.close()

                    except Exception as ex:
                        print('[ERROR] in DbThread (1):', ex)
                        connection = DbSource(self.dbConnectionInfo).getConnection()
                        # self.toDoStatements.append(sql)  # requeue for retry
                        self.toDoStatements.put(sql)  # requeue for retry

            else:
                time.sleep(1)

                numEmptyLoops += 1
                if numEmptyLoops > 60:
                    numEmptyLoops = 0

                    try:
                        cur = connection.cursor()
                        cur.execute('SELECT 1;')    # to prevent connection timeouts
                        cur.close()
                    except ex:
                        print(f"[ERROR] in DbThread (2):", ex)

        if connection:
            connection.commit()
            connection.close()

        print("DbThread terminated")
