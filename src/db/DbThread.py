"""
Created on Feb 5, 2015

@author: ibisek

Speeds-up DB inserts by not opening and closing cursors after every statement.
"""

import time
import threading
from db.DbSource import DbSource
import sys


class DbThread(threading.Thread):

    """
    @param dbConnectionInfo (optional) tuple of (host, port, dbName, dbUser, dbPassword)
    """
    def __init__(self, dbConnectionInfo: dict = None):
        super(DbThread, self).__init__()

        self.dbConnectionInfo = dbConnectionInfo
        
        self.toDoStatements = []
        self.toDoStatementsLock = threading.Lock()
        
        self.doRun = True

    def stop(self):
        self.doRun = False
        
    def addStatement(self, sql):
        with self.toDoStatementsLock:
            self.toDoStatements.append(sql)
            
    def run(self):
        connection = DbSource(self.dbConnectionInfo).getConnection()

        while self.doRun or len(self.toDoStatements) > 0:
            if len(self.toDoStatements) > 0:
                with self.toDoStatementsLock:

                    try:
                        cur = connection.cursor()
                        while len(self.toDoStatements) > 0:
                            sql = self.toDoStatements.pop()
                            print(f"[INFO] dbThread sql: {sql}")
                            try:
                                cur.execute(sql)
                            except Exception as ex:
                                sys.stderr.write("error in statement: %s\n" % sql)
                                sys.stderr.write(str(type(ex))+"\n")
                                sys.stderr.write(str(ex)+"\n")
                        connection.commit()
                        cur.close()

                    except Exception as e:
                        print('[ERROR] in DbThread:', e)
                        connection = DbSource(self.dbConnectionInfo).getConnection()

            else:
                time.sleep(1)

        if connection:
            connection.commit()
            connection.close()

        print("DbThread terminated")
