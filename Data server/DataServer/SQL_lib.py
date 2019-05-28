#!/usr/bin/python3
import pymysql
import pymssql
import threading
import logging

# Those class provide low level interface for execute query on DB (MySQL and MsSQL)
# Those class must be used through SQL module

# This class implement PyMySQL, for MySQL Server
class MySQL():
    def __init__(self, server, username, password, database, logger):
        self.__db = pymysql.connect(server = str(server), user = str(username), password = str(password), database = str(database))
        self.__db.autocommit(True)
        self.__lock = threading.Lock()
        self.__cursor = self.__db.cursor()
        self.__logger = logger

    def query(self, query, args = tuple()):
        try:
            self.__lock.acquire()
            self.__cursor.execute(query, args)
            self.__db.commit()
            self.__lock.release()
        except Exception as reason:
            self.__logger.error("Database transaction error")
            self.__logger.info("Reason: " + str(reason))
            self.__lock.release()
            return False

        try:
            result = self.__cursor.fetchall()
        except Exception as reason:
            result = True
        return result

# This class implement PyMsSQL, for Microsoft SQL Server
class MsSQL():
    def __init__(self, server, username, password, database, logger):
        self.__db = pymssql.connect(server = str(server), user = str(username), password = str(password), database = str(database))
        self.__db.autocommit(True)
        self.__lock = threading.Lock()
        self.__cursor = self.__db.cursor()
        self.__logger = logger

    def query(self, query, args = tuple()):
        try:
            if self.__lock.acquire(timeout = 120):
                self.__cursor.execute(query, args)
                self.__db.commit()
                self.__lock.release()
            else:
                raise Exception("Failed to aquire lock. Propably something is still pending")
        except Exception as reason:
            self.__logger.error("Database transaction error")
            self.__logger.info("Reason: " + str(reason))
            self.__lock.release()
            return False

        try:
            result = self.__cursor.fetchall()
        except Exception as reason:
            result = True
        return result