import SQL_lib
from random import randint
import datetime
#riceve numero sensore, tipo dato, dato & inserici nel DB + timestamp e numero casuale
#richiesta di dati per sensore , per tipo o per sensore/tipo o per range di data (in ogni caso ritorna sempre la data)

class CalvinoDB():
    def __init__(self, databaseAddress, databaseName, user, password):
        self.__dbAddress = databaseAddress
        self.__dbName = databaseName
        self.__dbUser = user
        self.__dbPass = password
        self.db = SQL_lib.MsSQL(server = self.__dbAddress, database = self.__dbName, username = self.__dbUser, password = self.__dbPass)

    def __randomN(self, digits):
        range_start = 10 **(digits - 1)
        range_end = (10 ** digits) - 1
        return randint(range_start, range_end)

    def insert(self, sensorNumber, dataType, value, timestamp = None):
        ID = self.__randomN(digits = 16)
        if timestamp == None:
            timestamp = str(datetime.datetime.utcnow() + datetime.timedelta(hours=+1))
            timestamp = "\'" + timestamp[:-7]  + "\'"   # Format timestamp in MS SQL 'datetime' format
        else:
            timestamp = "\'" + timestamp + "\'"
        queryResult = self.db.query('''INSERT INTO ''' + str(dataType) + ''' VALUES (''' + str(ID) + ''', ''' + str(sensorNumber) + ''', ''' + str(timestamp) + ''', ''' + str(value) + ''')''')
        if queryResult == True:         # Query succeded without output
            return True
        elif queryResult == False:      # Query failed
            return False
        else:                           # Query succeded with output
            return queryResult

    def request(self, sensorNumber, dataType, firstTime, lastTime):
        firstTime = "\'" + firstTime + "\'"
        lastTime = "\'" + lastTime + "\'"
        queryResult = self.db.query('''SELECT * FROM ''' + str(dataType) + ''' WHERE Timestamp >= ''' + str(firstTime) + ''' AND Timestamp <= ''' + str(lastTime) + ''' AND ID_sensore = ''' + str(sensorNumber))
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

    def summarize(self, sensorNumber, dataType, firstTime, lastTime):
        if firstTime >= lastTime:
            return (False, 1)
        else:
            many = self.request(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime)
            if many == True:
                return (False, 2)
            elif many == False:
                return (False, 3)
            else:
                rowNumber = 0
                mediumValue = 0
                for record in many:
                    rowNumber += 1
                    mediumValue = mediumValue + float(many[record][2])
                mediumValue = mediumValue / rowNumber
                mediumValue = round(number = mediumValue, ndigits = 2)
                result = self.remove(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime)
                if result == False:
                    return (False, 4)
                else:
                    result = self.insert(sensorNumber = sensorNumber, dataType = dataType, value = mediumValue, timestamp = firstTime)
                    if result == False:
                        return (False, 5)
                    else:
                        return (True, 0)
        

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
            print("Error: parsing error occured")
            print("Reason: " + str(reason))
            return False
        return parsed
