import threading
import socket
import time
import json
import re
import SQL

# This class provide a proxy interface between SQL handler class and others classes.
# This class also provide automatic parsing processes for data in both direction to
# avoid formal errors.
# For detailed informations about each method see documentation.
class dataProxy():
    def __init__(self, SQLProxy, syncEvents, lock, proxy):
        self.SQLProxy = SQLProxy
        self.lastData = dict()
        self.syncEvents = syncEvents
        self.proxyLock = lock
        self.proxy = proxy

        for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            self.lastData[i] = dict()
            self.lastData[i]['pressione'] = None
            self.lastData[i]['temperatura'] = None
            self.lastData[i]['altitudine'] = None
            self.lastData[i]['luce'] = None

    def lastDataUpdate(self, sensorNumber, dataType, dataValue):   
        if sensorNumber in self.lastData.keys():
            if str(dataType) not in self.lastData[sensorNumber].keys():
                return (False, 2)
            else:
                self.lastData[sensorNumber][dataType] = dataValue
                result = self.__DBinsert(sensorNumber = sensorNumber, dataType = dataType, dataValue = dataValue)
                if result == False:
                    return (False, 3)
                else:
                    self.__notifyUpdate(sensorNumber = sensorNumber, dataType = dataType, dataValue = dataValue)
                    return (True, 0)
        else:
            return (False, 1)

    def requestData(self, sensorNumber, dataType, firstTime, lastTime):
        if firstTime > lastTime:
            return(False, 1)
        else:
            if sensorNumber not in self.lastData.keys():
                return (False, 2)
            else:
                if dataType not in self.lastData[sensorNumber].keys():
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
        else:
            firstTime = str(firstTime)[:-7]
            match = re.match(pattern = r"([0-9]{4}\-[0-9]{2}\-[0-9]{2}\ [0-9]{2})\:[0-9]{2}\:[0-9]{2}", string = firstTime)
            firstTime = match.group(1) + ":00:00"
            lastTime = str(lastTime)[:-7]
            match = re.match(pattern = r"([0-9]{4}\-[0-9]{2}\-[0-9]{2}\ [0-9]{2})\:[0-9]{2}\:[0-9]{2}", string = lastTime)
            lastTime = match.group(1) + ":00:00"

            self.SQLProxy.notifySummarization(state = True)
            for sensorNumber in self.lastData.keys():
                for dataType in self.lastData[sensorNumber].keys():
                    result = self.SQLProxy.summarize(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime, skipCheck = True)
                    if result[0] == False:
                        if result[1] == 1:
                            print("SQL Error: Impossible to summarize values if firstTime is bigger than lastTime")
                        elif result[1] == 2:
                            print("SQL Error: No data to summarize for sensor " + str(sensorNumber) + " of type " + str(dataType) + " between " + str(firstTime) + " and " + str(lastTime))
                        elif result[1] == 3:
                            print("SQL Error: Unexpected query error while requesting data to summarize")
                        elif result[1] == 4:
                            print("SQL Error: Unexpected query error while removing summarized data")
                        elif result[1] == 5:
                            print("SQL Error: Unexpected query error while inserting new summarized data")
            self.SQLProxy.notifySummarization(state = False)
        print("Data optimized for interval " + str(firstTime) + " " + str(lastTime))
        return True


    def __notifyUpdate(self, sensorNumber, dataType, dataValue):
        self.proxyLock.acquire()
        self.proxy = [sensorNumber, dataType, dataValue]
        self.proxyLock.release()
        self.syncEvents.set()
        return

    def __DBinsert(self, sensorNumber, dataType, dataValue):
        result = self.SQLProxy.insert(sensorNumber = sensorNumber, dataType = dataType, value = dataValue, timestamp = None)
        return result
        

    def __DBrequest(self, sensorNumber, dataType, firstTime, lastTime):
        result = self.SQLProxy.request(sensorNumber = sensorNumber, dataType = dataType, firstTime = firstTime, lastTime = lastTime)
        return result


if __name__ == "__main__":
    print("Error: This program must be used as a module")
    quit()