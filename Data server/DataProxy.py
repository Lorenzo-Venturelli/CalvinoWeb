import threading
import socket
import time
import json
import SQL

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
                    while self.syncEvents.isSet() == True:
                        pass
                    self.syncEvents.set()
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
                        result = self.__parseQueryResult(queryResult = result)
                        try:
                            result = json.dumps(result)
                        except json.JSONDecodeError:
                            return (False, 6)
                        print(result)
                        return (True, result)

    def __notifyUpdate(self, sensorNumber, dataType, dataValue):
        self.proxyLock.acquire()
        self.proxy = [sensorNumber, dataType, dataValue]
        self.proxyLock.release()
        self.syncEvents.set()
        return

    def __DBinsert(self, sensorNumber, dataType, dataValue):
        result = self.SQLProxy.insert(tipo = dataType, sensore = sensorNumber, valore = dataValue)
        return result

    def __DBrequest(self, sensorNumber, dataType, firstTime, lastTime):
        result = self.SQLProxy.request(dataI = firstTime, dataF = lastTime, sensore = sensorNumber, tipo = dataType)
        return result

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
            print(parsed)
        except Exception as reason:
            print("Eccezzione : " + str(reason))
        return parsed
                


if __name__ == "__main__":
    print("Error: This program must be used as a module")
    quit()