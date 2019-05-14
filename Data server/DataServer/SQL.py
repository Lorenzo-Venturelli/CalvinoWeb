#! /usr/bin/python
import SQL_lib
import queue
from random import randint
import datetime
import logging

# This class provide method to execute SQL DB operations.
# This class provide building query method and parsing method.
# This class must be used through DataProxy interface to avodi errors.
# For detailed informations about each method see documentation.
class CalvinoDB():
    def __init__(self, databaseAddress, databaseName, user, password, loggingFile):
        self.__dbAddress = databaseAddress
        self.__dbName = databaseName
        self.__dbUser = user
        self.__dbPass = password
        self.__queryQueue = queue.Queue()
        self.__pauseInsert = False
        self.__logger = logging.getLogger(name = "SQL")
        self.__logger.basicConfig(filename = loggingFile, level = logging.INFO)
        self.db = SQL_lib.MsSQL(server = self.__dbAddress, database = self.__dbName, username = self.__dbUser, password = self.__dbPass, logger = self.__logger)

    def __randomN(self, digits):
        range_start = 10 **(digits - 1)
        range_end = (10 ** digits) - 1
        return randint(range_start, range_end)

    def insert(self, sensorNumber, dataType, value, timestamp = None):
        ID = self.__randomN(digits = 16)
        if timestamp == None:
            timestamp = str(datetime.datetime.now())
            timestamp = "\'" + timestamp[:-7]  + "\'"   # Format timestamp in MS SQL 'datetime' format
        else:
            timestamp = "\'" + timestamp + "\'"

        query = '''INSERT INTO ''' + str(dataType) + ''' VALUES (''' + str(ID) + ''', ''' + str(sensorNumber) + ''', ''' + str(timestamp) + ''', ''' + str(value) + ''')'''
        if self.__pauseInsert == True:
            self.__queryQueue.put(query)
            return True
        else:
            queryResult = self.db.query(query)
            if queryResult == True:         # Query succeded without output
                return True
            elif queryResult == False:      # Query failed
                return False
            else:                           # Query succeded with output
                return queryResult

    def request(self, sensorNumber, dataType, firstTime, lastTime):
        firstTime = "\'" + firstTime + "\'"
        lastTime = "\'" + lastTime + "\'"
        self.notifySummarization(state = True)
        queryResult = self.db.query('''SELECT * FROM ''' + str(dataType) + ''' WHERE Timestamp >= ''' + str(firstTime) + ''' AND Timestamp <= ''' + str(lastTime) + ''' AND ID_sensore = ''' + str(sensorNumber))
        self.notifySummarization(state = False)
        if queryResult == True:         # Query succeded without output
            return True
        elif queryResult == False:      # Query failed
            return False
        else:                           # Query succeded with output
            parsedResult = self.__parseQueryResult(queryResult = queryResult)
            if parsedResult == False:
                return False
            else:
                return (parsedResult)

    def remove(self, sensorNumber, dataType, firstTime, lastTime):
        firstTime = "\'" + firstTime + "\'"
        lastTime = "\'" + lastTime + "\'"
        queryResult = self.db.query('''DELETE FROM ''' + str(dataType) + ''' WHERE Timestamp >= ''' + str(firstTime) + ''' AND Timestamp <= ''' + str(lastTime) + ''' AND ID_sensore = ''' + str(sensorNumber))

        if queryResult == True:         # Query succeded without output
            return True
        elif queryResult == False:      # Query failed
            return False
        else:                           # Query succeded with output
            return queryResult

    def summarize(self, sensorNumber, dataType, firstTime, lastTime, skipCheck = False):
        if firstTime >= lastTime and skipCheck == False:
            status = (False, 1)
        else:
            self.__pauseInsert = True
            many = self.request(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime)
            if many == True:
                status = (False, 2)
            elif many == False:
                status = (False, 3)
            else:
                rowNumber = 0
                mediumValue = 0
                for record in many:
                    rowNumber += 1
                    mediumValue = mediumValue + float(many[record][2])
                if rowNumber != 0:
                    mediumValue = mediumValue / rowNumber
                    mediumValue = round(number = mediumValue, ndigits = 2)
                    result = self.remove(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime)
                    if result == False:
                        status = (False, 4)
                    else:
                        result = self.insert(sensorNumber = sensorNumber, dataType = dataType, value = mediumValue, timestamp = firstTime)
                        if result == False:
                            status = (False, 5)
                        else:
                            status = (True, 0)
                else:
                    status = (True, 0)
        return status

    def notifySummarization(self, state):
        if state == True:
            self.__pauseInsert = True
        else:
            self.__pauseInsert = False
            self.__flushQueue()
            
    def __flushQueue(self):
        while self.__queryQueue.empty() == False:
            query = self.__queryQueue.get()
            queryResult = self.db.query(query)
            if queryResult == False:
                self.__logger.warning("Unknown SQL error while inserting queued data")
        
    def __parseQueryResult(self, queryResult):
        parsed = dict()
        tmp = dict()

        try:
            for entry in queryResult:
                tmp[entry[0]] = entry[1:]

            for entry in tmp.keys():
                parsed[entry] = []
                for element in tmp[entry]:
                    parsed[entry].append(str(element))
        except Exception as reason:
            self.__logger.warning("parsing error occured")
            self.__logger.info("Reason: " + str(reason))
            return False
        return parsed
