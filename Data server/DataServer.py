#! /usr/bin/python
import threading
import socket
import time
import json
import re
import datetime
import DataProxy
import MQTT
import SQL
import encriptionHandler

startingTime = datetime.datetime.utcnow() + datetime.timedelta(hours = +1)

class DataServerAccepter(threading.Thread):
    def __init__(self, address, port, dataProxy, dataProxyLock, dataProxySyncEvent):
        self.serverAddress = address
        self.serverPort = port
        self.dataProxy = dataProxy
        self.dataProxyLock = dataProxyLock
        self.dataProxySyncEvent = dataProxySyncEvent
        self.serverSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
        self.__running = True
        self.connectedClient = dict()
        threading.Thread.__init__(self, name = "Data Server Accepter Thread", daemon = False)

    def run(self):
        try:
            self.serverSocket.bind((str(self.serverAddress), int(self.serverPort)))
        except socket.error as reason:
            print("Fatal error: Data server accepter socket failed to bind")
            print("Reason: " + str(reason))
            return

        self.dataProxySyncEvent.set()
        self.serverSocket.listen(5)
        while self.__running == True:
            try:
                clientSocket, clientAddress = self.serverSocket.accept()
            except socket.error():
                print("Error: Unknown error occurred while a client tried to connect. Connection aborted")
                clientAddress = None
            
            if clientAddress != None:
                try:
                    clientThread = DataClient(address = clientAddress, clientSocket = clientSocket, dataProxy = self.dataProxy, dataProxyLock = self.dataProxyLock, dataProxySyncEvent = self.dataProxySyncEvent)
                    clientThread.start()
                    self.connectedClient[str(clientAddress[0])] = clientThread
                    print("Client " + str(clientAddress[0]) + " connected")
                except Exception as reason:
                    print("Error: Unhandled error occured while creating client thread for client " + str(clientAddress[0]))
                    print("Reason: " + str(reason))
                    clientSocket.close()
                    clientSocket = None
                    clientAddress = None
                
            self.__garbageCollector()

        self.__garbageCollector()
        return
    
    def __garbageCollector(self):
        deathClient = []
        for client in self.connectedClient.keys():
            if self.connectedClient[client].clientConnected == False:
                deathClient.append(client)
        
        for client in deathClient:
            del self.connectedClient[client]

        return

    def stop(self):
        self.__running = False
        fakeClient = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
        fakeClient.connect(("127.0.0.1", self.serverPort))

        for client in self.connectedClient:
            self.connectedClient[client].disconnect()
            self.connectedClient[client].join()

        fakeClient.close()
        return
         
class DataClient(threading.Thread):
    def __init__(self, address, clientSocket, dataProxy, dataProxyLock, dataProxySyncEvent):
        self.address = address
        self.clientSocket = clientSocket
        self.dataProxy = dataProxy
        self.dataProxyLock = dataProxyLock
        self.dataProxySyncEvent = dataProxySyncEvent
        self.clientConnected = True
        self.myPubKey = None
        self.myPrivKey = None
        self.hisPubKey = None
        threading.Thread.__init__(self, name = "Data Client " + str(address[0]), daemon = True)

    def disconnect(self):
        self.clientConnected = False
        self.clientSocket.close()
        return

    def __rsaKeyHandShake(self):
        self.clientSocket.sendall(str("199").encode())
        answer = self.clientSocket.recv(1024)
        if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
            answer = answer.decode()
            if answer == "200":
                (self.myPubKey, self.myPrivKey) = encriptionHandler.generateRSA()
                self.clientSocket.sendall(str(self.myPubKey).encode())
                answer = self.clientSocket.recv(1024)
                if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                    answer = answer.decode()
                    answer = encriptionHandler.RSAdecrypt(privkey = self.myPrivKey, secret = answer)
                    if answer != False:
                        self.hisPubKey = answer
                        self.clientSocket.sendall(str("200").encode())
                        return True
                    else:
                        self.clientSocket.sendall(str("599").encode())
        print("Security error: Error occurred while negotiating RSA keys with " + str(self.clientSocket[0]) + " connection terminated for security reasons")
        return False
    
    def run(self):
        resutl = self.__rsaKeyHandShake()
        if result == False:
            self.disconnect()
        else:
            while self.clientConnected == True:
                try:
                    request = self.clientSocket.recv(1024)
                except ConnectionResetError:
                    self.disconnect()
                    continue
                except Exception:
                    print("Error: Unknown comunication error occurred with client " + str(self.address[0]))
                    continue

                if request != None and request != 0 and request != '' and request != str.encode(''):
                    request = request.decode()
                    try:
                        request = json.loads(request)
                    except json.JSONDecodeError:
                        print("Error: Received corrupted request from host " + str(self.address[0]))
                        continue

                    if "SN" in request.keys() and "DT" in request.keys() and "FT" in request.keys() and "LT" in request.keys():
                        if request["SN"] != None and request["DT"] != None and request["FT"] != None and request["LT"] != None:       
                            result = self.dataProxy.requestData(sensorNumber = request["SN"], dataType = request["DT"], firstTime = request["FT"], lastTime = request["LT"])
                            if result[0] == True:
                                result = result[1]
                                status = "200"
                            else:
                                if result[1] == 1 or result[1] == 2 or result[1] == 3:
                                    status = "499"
                                elif result[1] == 4 or result[1] == 5 or result[1] == 5:
                                    status = "399"
                                result = dict()
                        else:
                            result = dict()
                            status = "599"
                    else:
                        result = dict()
                        status = "599"

                    resultJSON = json.dumps(result)
                    resultJSON = resultJSON.encode()
                    status = str(status).encode()
                    self.clientSocket.sendall(resultJSON)
                    self.clientSocket.sendall(status)
                    
                    try:
                        response = self.clientSocket.recv(1024)
                    except ConnectionResetError:
                        self.disconnect()
                        continue
                    except Exception:
                        print("Error: Unknown comunication error occurred with client " + str(self.address[0]))
                        continue

                    if response != None and response != 0 and response != '' and request != str.encode(''):
                        response = response.decode()
                        if response == "200":
                            continue
                        else:
                            self.clientSocket.sendall(resultJSON)
                            self.clientSocket.sendall(status)
                            continue
                else:
                    self.disconnect()
        
        print("Client " + str(self.address[0]) + " disconnected")
        return




def optimizeSQL(dataProxy, reason, firstTime = None):
    if reason == True:
        if firstTime != None:
            lastTime = firstTime + datetime.timedelta(hours = +1)
        else:
            return False
    else:
        lastTime = datetime.datetime.utcnow() + datetime.timedelta(hours = +1)
        firstTime = datetime.datetime.utcnow()

    result = dataProxy.summarizeData(firstTime = firstTime, lastTime = lastTime)
    if result == True and reason == True:
        firstTime = firstTime + datetime.timedelta(hours = +1)
        lastTime = lastTime + datetime.timedelta(hours = +1)
        result = dataProxy.summarizeData(firstTime = firstTime, lastTime = lastTime)

    startingTime = datetime.datetime.utcnow() + datetime.timedelta(hours = +1)
    return result

def shutdown(mqttHandler, dataProxyHandler, dataServerListener, startingTime):
    mqttHandler.stop()
    dataServerListener.stop()
    mqttHandler.join()
    dataServerListener.join()
    optimizeSQL(dataProxy = dataProxyHandler, reason = True, firstTime = startingTime)
    return

if __name__ == "__main__":
    mqttSyncEvent = [threading.Event(), threading.Event()]
    dataProxySyncEvent = threading.Event()
    dataProxyLock = threading.Lock()
    lastData = None

    try:
        with open(file = "./file/settings.json", mode = 'r') as settingsFile:
            settings = json.load(fp = settingsFile)
    except FileNotFoundError:
        print("Error: Settings file not found")
        settings = dict()
    except json.JSONDecodeError:
        print("Error: Settings file has an invalid format")
        settings = dict()
    except Exception:
        print("Error: An unknown error occurred while reading the settings file")
        settings = dict()

    if "brkAdr" in settings.keys():
        brkAdr = settings["brkAdr"]
    else:
        print('''Error: No broker address is present in settings file! Please provide it''')
        brkAdr = input(prompt = "> ")

    if "brkUsername" in settings.keys():
        brkUsername = settings["brkUsername"]
    else:
        print('''Error: No broker username is present in settings file! Please provide it''')
        brkUsername = input(prompt = "> ")

    if "brkPassword" in settings.keys():
        brkPassword = settings["brkPassword"]
    else:
        print('''Error: No broker password is present in settings file! Please provide it''')
        brkPassword = input(prompt = "> ")

    if "sqlAdr" in settings.keys():
        sqlAdr = settings["sqlAdr"]
    else:
        print('''Error: No SQL Server address is present in settings file! Please provide it''')
        sqlAdr = input(prompt = "> ")

    if "sqlUsername" in settings.keys():
        sqlUsername = settings["sqlUsername"]
    else:
        print('''Error: No SQL username is present in settings file! Please provide it''')
        sqlUsername = input(prompt = "> ")

    if "sqlPassword" in settings.keys():
        sqlPassword = settings["sqlPassword"]
    else:
        print('''Error: No SQL password is present in settings file! Please provide it''')
        sqlPassword = input(prompt = "> ")

    if "sqlName" in settings.keys():
        sqlName = settings["sqlName"]
    else:
        print('''Error: No SQL DB Name is present in settings file! Please provide it''')
        sqlName = input(prompt = "> ")

    try:
        sqlHandler = SQL.CalvinoDB(databaseAddress = sqlAdr, databaseName = sqlName, user = sqlUsername, password = sqlPassword)
    except Exception as reason:
        print("Fatal error: SQL initialization error")
        print("Reason: " + str(reason))
        quit()

    try:
        dataProxyHandler = DataProxy.dataProxy(SQLProxy = sqlHandler, syncEvents = dataProxySyncEvent, lock = dataProxyLock, proxy = lastData)
    except Exception as reason:
        print("Fatal error: Data Proxy initialization error")
        print("Reason: " + str(reason))
        quit()
    
    try:
        mqttHandler = MQTT.MQTTclient(brokerAddress = brkAdr, username = brkUsername, password = brkPassword, syncEvents = mqttSyncEvent, dataProxy = dataProxyHandler)
    except Exception as reason:
        print("Fatal error: MQTT initialization error")
        print("Reason: " + str(reason))
        quit()

    try:
        dataServerListener = DataServerAccepter(address = '', port = 2000, dataProxy = dataProxyHandler, dataProxyLock = dataProxyLock, dataProxySyncEvent = dataProxySyncEvent)
    except Exception as reason:
        print("Fatal error: Data Server can not be started")
        print("Reason: " +  str(reason))
        quit()

    mqttHandler.start()

    mqttSyncEvent[0].wait(timeout = None)
    if mqttSyncEvent[1].is_set() == True:
        print("Fatal error: MQTT connection initialization error")
        print("Server stopped because fatal MQTT connection error")
        quit()
    else:
        print("MQTT connection initialized")
        mqttSyncEvent[0].clear()
        mqttSyncEvent[1].clear()

        if dataProxySyncEvent.is_set == True:
            dataProxySyncEvent.clear()

        dataServerListener.start()

        if dataProxySyncEvent.wait(timeout = 2) == False:
            print("Fatal error: Data Server can not bind address")
            mqttHandler.stop()
            mqttHandler.join()
            print("Server stopped because of fatal socket error")
            quit()
        else:
            try:
                while True:
                    time.sleep(3600)
                    optimizeSQL(dataProxy = dataProxyHandler, reason = False)
            except KeyboardInterrupt:
                shutdown(mqttHandler = mqttHandler, dataProxyHandler = dataProxyHandler, dataServerListener = dataServerListener, startingTime = startingTime)
                print("Server stopped because of user")
                quit()

        
