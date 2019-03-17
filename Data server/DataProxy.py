import threading
import socket
import time
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

    def __notifyUpdate(self, sensorNumber, dataType, dataValue):
        self.proxyLock.acquire()
        self.proxy = [sensorNumber, dataType, dataValue]
        self.proxyLock.release()
        self.syncEvents.set()
        return

    def __DBinsert(self, sensorNumber, dataType, dataValue):
        result = self.SQLProxy.insert(tipo = dataType, sensore = sensorNumber, valore = dataValue)
        return result

if __name__ == "__main__":
    print("Error: This program must be used as a module")
    quit()