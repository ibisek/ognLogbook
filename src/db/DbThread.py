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
        
        if not dbConnectionInfo:
            self.connection = DbSource().getConnection()
        else:
            dbSource = DbSource(dbConnectionInfo)
            #dbSource.setDbConnectionInfo(dbConnectionInfo)
            self.connection = dbSource.getConnection()
        
        self.toDoStatements = []
        self.toDoStatementsLock = threading.Lock()
        
        self.doRun = True

    def stop(self):
        self.doRun = False
        
    def __del__(self):
        if self.connection:
            self.connection.commit()
            self.connection.close()

    def addStatement(self, sql):
        with self.toDoStatementsLock:
            self.toDoStatements.append(sql)
            
    def run(self):
        while self.doRun or len(self.toDoStatements) > 0:
            if len(self.toDoStatements) > 0:
                with self.toDoStatementsLock:
                    cur = self.connection.cursor()
                    while len(self.toDoStatements) > 0:
                        sql = self.toDoStatements.pop()
                        try:
                            cur.execute(sql)
                        except Exception as ex:
                            sys.stderr.write("error in statement: %s\n" % sql)
                            sys.stderr.write(str(type(ex))+"\n")
                            sys.stderr.write(str(ex)+"\n")
                    self.connection.commit()
                    cur.close()
            else:
                time.sleep(1)
        
        print("DbThread terminated")
