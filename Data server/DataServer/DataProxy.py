#!/usr/bin/python3
import threading, socket, time, json, re, logging, datetime
import SQL

# This class provide a proxy interface between SQL handler class and others classes.
# This class also provide automatic parsing processes for data in both direction to
# avoid formal errors.
class dataProxy():
    def __init__(self, SQLProxy, syncEvents, lock, proxy, loggingFile):
        self.__SQLProxy = SQLProxy
        self.__lastData = dict()
        self.__syncEvents = syncEvents
        self.__lastSumm = datetime.datetime.now()
        self.__logger = logging.getLogger(name = "DataProxy")
        logging.basicConfig(filename = loggingFile, level = logging.INFO)

        for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            self.__lastData[i] = dict()
            self.__lastData[i]['pressione'] = None
            self.__lastData[i]['temperatura'] = None
            self.__lastData[i]['altitudine'] = None
            self.__lastData[i]['luce'] = None

    def lastDataUpdate(self, sensorNumber, dataType, dataValue):   
        if sensorNumber in self.__lastData.keys():
            if str(dataType) not in self.__lastData[sensorNumber].keys():
                return (False, 2)
            else:
                self.__lastData[sensorNumber][dataType] = dataValue
                result = self.__DBinsert(sensorNumber = sensorNumber, dataType = dataType, dataValue = dataValue)
                if result == False:
                    return (False, 3)
                else:
                    return (True, 0)
        else:
            return (False, 1)

    def requestData(self, sensorNumber, dataType, firstTime, lastTime):
        if firstTime > lastTime:
            return(False, 1)
        else:
            if sensorNumber not in self.__lastData.keys():
                return (False, 2)
            else:
                if dataType not in self.__lastData[sensorNumber].keys():
                    return (False, 3)
                else:
                    result = self.__DBrequest(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime)
                    if result == True:
                        return (False, 4)
                    elif result == False:
                        return (False, 5)
                    else:
                        return (True, result)

    def summarizeData(self, firstTime, lastTime, skipCheck = False):
        if firstTime >= lastTime:
            return False
        elif self.__lastSumm <= lastTime or skipCheck == True:
            firstTime = str(firstTime)[:-7]
            match = re.match(pattern = r"([0-9]{4}\-[0-9]{2}\-[0-9]{2}\ [0-9]{2})\:[0-9]{2}\:[0-9]{2}", string = firstTime)
            firstTime = str(match.group(1)) + ":00:00"

            lastTime = str(lastTime)[:-7]
            match = re.match(pattern = r"([0-9]{4}\-[0-9]{2}\-[0-9]{2}\ [0-9]{2})\:[0-9]{2}\:[0-9]{2}", string = lastTime)
            lastTime = str(match.group(1)) + ":00:00"

            try:
                self.__SQLProxy.notifySummarization(status = True)
                for sensorNumber in self.__lastData.keys():
                    for dataType in self.__lastData[sensorNumber].keys():
                        result = [None, None]
                        attemps = 0
                        while result[0] != True and attemps < 3:
                            attemps = attemps + 1
                            result = self.__SQLProxy.summarize(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime, skipCheck = True)
                            if result[0] == False:
                                if result[1] == 1:
                                    self.__logger.warning("Impossible to summarize values if firstTime is bigger than lastTime")
                                elif result[1] == 2:
                                    self.__logger.warning("No data to summarize for sensor " + str(sensorNumber) + " of type " + str(dataType) + " between " + str(firstTime) + " and " + str(lastTime))
                                elif result[1] == 3:
                                    self.__logger.warning("Unexpected query error while requesting data to summarize")
                                elif result[1] == 4:
                                    self.__logger.warning("Unexpected query error while removing summarized data")
                                elif result[1] == 5:
                                    self.__logger.warning("Unexpected query error while inserting new summarized data")
                                elif result[1] == 6:
                                    self.__logger.warning("Unexpected query error while while sumarizing data")
                self.__SQLProxy.notifySummarization(status = False)
                self.__logger.info("Data optimized for interval " + str(firstTime) + " " + str(lastTime))
                self.__lastSumm = datetime.datetime.now()
                return True
            except Exception:
                self.__logger.error("Unknown error occurred while summarizing")
                return False
        else:
            return False

    def __DBinsert(self, sensorNumber, dataType, dataValue):
        result = self.__SQLProxy.insert(sensorNumber = sensorNumber, dataType = dataType, value = dataValue, timestamp = None)
        return result
        
    def __DBrequest(self, sensorNumber, dataType, firstTime, lastTime):
        if self.__SQLProxy.waitForSummarization() == True:
            result = self.__SQLProxy.request(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime)
            return result
        else:
            return False

if __name__ == "__main__":
    print("Error: This program must be used as a module")
    quit()