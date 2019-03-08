import threading
import socket
import time

class dataProxy():
    def __init__(self, SQLProxy, syncEvents, lock, proxy):
        self.SQLProxy = SQLProxy
        self.lastData = dict()
        self.syncEvents = syncEvents
        self.proxyLock = lock
        self.proxy = proxy

        for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            self.lastData[i] = dict()
            self.lastData[1]['pressione'] = None
            self.lastData[1]['temperatura'] = None
            self.lastData[1]['altitudine'] = None
            self.lastData[1]['luce'] = None

    def lastDataUpdate(self, sensorNumber, dataType, dataValue):
        if sensorNumber not in self.lastData.keys():
            print("Error: Sensor do not exist")
            return (False, 1)
        else:
            if dataType not in self.lastData[sensorNumber].keys():
                print("Error: Data type do not exist for sensor " + str(sensorNumber))
                return (False, 2)
            else:
                self.lastData[sensorNumber][dataType] = dataValue
                #result = self.__DBupdate(sensorNumber, dataType, dataValue)
                if result == False:
                    print("Error: SQL database error, this piece of data is lost")
                    return (False, 3)
                else:
                    self.__notifyUpdate(sensorNumber = sensorNumber, dataType = dataType, dataValue = dataValue)
                    return (True, 0)

    def __notifyUpdate(self, sensorNumber, dataType, dataValue):
        self.lock.acquire()
        self.proxy = [sensorNumber, dataType, dataValue]
        self.lock.release()
        self.syncEvents.set()
        return


if __name__ == "__main__":
    print("Error: This program must be used as a module")
    quit()