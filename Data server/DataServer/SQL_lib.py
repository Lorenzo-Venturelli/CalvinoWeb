#! /usr/bin/python
import pymysql
import pymssql
import threading

# Those class provide low level interface for execute query on DB (MySQL and MsSQL)
# Those class must be used through SQL module

class MySQL():
    def __init__(self, server, username, password, database):
        self.__db = pymysql.connect(server = str(server), user = str(username), password = str(password), database = str(database))
        self.__db.autocommit(True)
        self.__lock = threading.Lock()
        self.__cursor = self.__db.cursor()

    def query(self, query, args = tuple()):
        try:
            self.__lock.acquire()
            self.__cursor.execute(query, args)
            self.__db.commit()
            self.__lock.release()
        except Exception as reason:
            print(reason)
            self.__lock.release()
            return False

        try:
            result = self.__cursor.fetchall()
        except Exception as reason:
            result = True
            #print(reason)
        return result

# This class implement PyMsSQL, for Microsoft SQL Server
class MsSQL():
    def __init__(self, server, username, password, database):
        self.__db = pymssql.connect(server = str(server), user = str(username), password = str(password), database = str(database))
        self.__db.autocommit(True)
        self.__lock = threading.Lock()
        self.__cursor = self.__db.cursor()

    def query(self, query, args = tuple()):
        try:
            self.__lock.acquire()
            self.__cursor.execute(query, args)
            self.__db.commit()
            self.__lock.release()
        except Exception as reason:
            print(reason)
            self.__lock.release()
            return False

        try:
            result = self.__cursor.fetchall()
        except Exception as reason:
            result = True
            #print(reason)
        return result