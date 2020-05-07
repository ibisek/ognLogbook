'''
Created on Aug 15, 2014

@author: ibisek
'''

import os

# native (C) mysql lib:
# import MySQLdb

# python-based mysql lib (replacement so it works in PyPy):
import pymysql
pymysql.install_as_MySQLdb()


class DbSource(object):

    connection = None
    
    def __init__(self, dbConnectionInfo = None):

        if dbConnectionInfo:
            self.setDbConnectionInfo(dbConnectionInfo)

        else:
            self.HOST = os.environ.get('DB_HOST', None)
            self.PORT = int(os.environ.get('DB_PORT', None))
            self.DB_NAME = os.environ.get('DB_NAME', None)
            self.DB_USER = os.environ.get('DB_USER', None)
            self.DB_PASSWD = os.environ.get('DB_PASSWORD', None)

            self.dbOpenConnection()

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
        
        if self.connection: self.connection.close()
        self.dbOpenConnection()

    def dbOpenConnection(self):
        # self.connection = MySQLdb.connect(host=self.HOST, port=self.PORT, user=self.DB_USER, passwd=self.DB_PASSWD, db=self.DB_NAME)
        self.connection = pymysql.connect(host=self.HOST, port=self.PORT, user=self.DB_USER, passwd=self.DB_PASSWD, database=self.DB_NAME, autocommit=True)
        
    def getConnection(self):
        return self.connection
        
    def dbCloseConnection(self):
        self.connection.close()
