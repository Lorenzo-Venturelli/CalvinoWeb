#!/usr/bin/python3
import pymysql, pymssql,threading, logging

# Those class provide low level interface for execute query on DB (MySQL and MsSQL)
# Those class must be used through SQL module

# This class implement PyMySQL, for MySQL Server (It is not up to date, see MsSQL class)
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
        try:
            self.__db = pymssql.connect(server = str(server), user = str(username), password = str(password), database = str(database))
        except Exception:
            raise Exception("Impossible to create a connection with DB")
        self.__db.autocommit(True)
        self.__lock = threading.Lock()
        self.__cursor = self.__db.cursor()
        self.__logger = logger

    def query(self, query, args = tuple()):
        if self.__lock.acquire(timeout = 120):
            try:
                self.__cursor.execute(query, args)
                self.__db.commit()
            except Exception as reason:
                self.__logger.error("Database transaction error")
                self.__logger.info("Reason: " + str(reason))
                return False
            try:
                self.__lock.release()
            except RuntimeError:
                pass
            except Exception:
                pass
            try:
                result = self.__cursor.fetchall()
            except Exception as reason:
                result = True
            return result
        else:
            try:
                self.__lock.release()
            except RuntimeError:
                pass
            except Exception:
                pass
            return False