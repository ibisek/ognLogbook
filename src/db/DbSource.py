'''
Created on Aug 15, 2014

@author: ibisek
'''

import os
import sys
import sqlite3

# native (C) mysql lib:
# import MySQLdb

# python-based mysql lib (replacement so it works in PyPy):
import pymysql
pymysql.install_as_MySQLdb()


class DbSource(object):

    connection = None
    
    def __init__(self, dbConnectionInfo=None):

        if dbConnectionInfo:
            self.setDbConnectionInfo(dbConnectionInfo)

        else:
            if 'DB_HOST' in os.environ:
                self.HOST = os.environ.get('DB_HOST', None)
            if 'DB_PORT' in os.environ:
                self.PORT = int(os.environ.get('DB_PORT', 3306))
            if 'DB_NAME' in os.environ:
                self.DB_NAME = os.environ.get('DB_NAME', None)
            if 'DB_USER' in os.environ:
                self.DB_USER = os.environ.get('DB_USER', None)
            if 'DB_PASSWORD' in os.environ:
                self.DB_PASSWD = os.environ.get('DB_PASSWORD', None)

    '''
    @param dbConnectionInfo tuple of (host, port, dbName, dbUser, dbPassword) 
    '''        
    def setDbConnectionInfo(self, dbConnectionInfo):
        (host, port, dbName, dbUser, dbPassword) = dbConnectionInfo
        self.HOST = host
        self.PORT = port
        self.DB_NAME = dbName
        self.DB_USER = dbUser
        self.DB_PASSWD = dbPassword
        
        if self.connection:
            self.connection.close()

    def _getConnectionMysql(self):
        # self.connection = MySQLdb.connect(host=self.HOST, port=self.PORT, user=self.DB_USER, passwd=self.DB_PASSWD, db=self.DB_NAME)
        return pymysql.connect(host=self.HOST, port=self.PORT, user=self.DB_USER, passwd=self.DB_PASSWD, database=self.DB_NAME, autocommit=True)
        
    def getConnection(self):
        # return self.connection

        if 'SQLITE_DB_FILENAME' in os.environ:
            return DbSource._getConnectionSqlite()
        else:
            return self._getConnectionMysql()

    def dbCloseConnection(self):
        self.connection.close()

    @staticmethod
    def _getConnectionSqlite():
        conn = None

        if 'SQLITE_DB_FILENAME' not in os.environ:
            raise ValueError('[ERROR] SQLITE_DB_FILENAME env variable not defined!')

        dbFilename = os.environ.get('SQLITE_DB_FILENAME')

        try:
            conn = sqlite3.connect(dbFilename)
        except sqlite3.OperationalError as e:
            print("ARCHIVE_DB_FILENAME:", dbFilename)
            sys.stderr.write("Error: {}\n".format(str(e)))

        return conn
