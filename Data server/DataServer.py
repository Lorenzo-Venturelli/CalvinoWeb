import threading
import socket
import time
import json
import DataProxy
import MQTT
import SQL

class DataServerAccepter(threading.Thread):
    def __init__(self, address, port, dataProxy, dataProxyLock, dataProxySyncEvent):
        self.serverAddress = address
        self.serverPort = port
        self.dataProxy = dataProxy
        self.dataProxyLock = dataProxyLock
        self.dataProxySyncEvent = dataProxySyncEvent
        self.serverSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
        self.running = True
        self.connectedClient = []
        threading.Thread.__init__(self, name = "Data Server Accepter Thread", daemon = False)

    def run(self):
        try:
            self.serverSocket.bind((str(self.serverAddress), int(self.serverPort)))
        except socket.error:
            print("Fatal error: Data server accepter socket failed to bind")
            quit()

        self.serverSocket.listen(5)
        while self.running == True:
            try:
                clientSocket, clientAddress = self.serverSocket.accept()
            except socket.error():
                print("Error: Unknown error occurred while a client tried to connect. Connection aborted")
                clientAddress = None
            
            if clientAddress != None:
                try:
                    clientThread = DataClient(address = clientAddress, clientSocket = clientSocket, dataProxy = self.dataProxy, dataProxyLock = self.dataProxyLock, dataProxySyncEvent = self.dataProxySyncEvent)
                    clientThread.start()
                    self.connectedClient.append(clientThread)
                except Exception as reason:
                    print("Error: Unhandled error occured while creating client thread for client " + str(clientAddress[0]))
                    print("Reason: " + str(reason))
                    clientSocket.close()
                    clientSocket = None
                    clientAddress = None

            
class DataClient(threading.Thread):
    def __init__(self, address, clientSocket, dataProxy, dataProxyLock, dataProxySyncEvent):
        self.address = address
        self.clientSocket = clientSocket
        self.dataProxy = dataProxy
        self.dataProxyLock = dataProxyLock
        self.dataProxySyncEvent = dataProxySyncEvent
        threading.Thread.__init__(self, name = "Data Client " + str(address[0]), daemon = True)
    
    def run(self):
        while True:
            ##

if __name__ == "__main__":
    mqttSyncEvent = [threading.Event(), threading.Event()]
    dataProxySyncEvent = threading.Event()
    dataProxyLock = threading.Lock()
    lastData = None

    try:
        with open(file = "./file/settings.json", mode = 'r') as settingsFile:
            settings = json.load(fp = settingsFile)
    except FileNotFoundError:
        print("Error: Settings file not found, assuming standard settings")
        settings = dict()
    except json.JSONDecodeError:
        print("Error: Settings file has an invalid format, assuming standard settings")
        settings = dict()
    except Exception:
        print("Error: An unknown error occurred while reading the settings file, assuming standard settings")
        settings = dict()

    if "brkAdr" in settings.keys():
        brkAdr = settings["brkAdr"]
    else:
        print('''Error: No broker address is present in settings file! Assuming "broker.shiftr.io"''')
        brkAdr = "broker.shiftr.io"

    if "brkUsername" in settings.keys():
        brkUsername = settings["username"]
    else:
        print('''Error: No broker username is present in settings file! Assuming "calvino00"''')
        brkUsername = "calvino00"

    if "brkPassword" in settings.keys():
        brkPassword = settings["password"]
    else:
        print('''Error: No broker password is present in settings file! Assuming "0123456789"''')
        brkPassword = "0123456789"

    if "sqlAdr" in settings.keys():
        sqlAdr = settings["sqlAdr"]
    else:
        print('''Error: No SQL Server address is present in settings file! Assuming "51.145.135.119"''')
        sqlAdr = "51.145.135.119"

    if "sqlUsername" in settings.keys():
        sqlUsername = settings["sqlUsername"]
    else:
        print('''Error: No SQL username is present in settings file! Assuming "SA"''')
        sqlUsername = "SA"

    if "sqlPassword" in settings.keys():
        sqlPassword = settings["sqlPassword"]
    else:
        print('''Error: No SQL password is present in settings file! Assuming "Fermi3f27"''')
        sqlPassword = "Fermi3f27"

    if "sqlName" in settings.keys():
        sqlName = settings["sqlName"]
    else:
        print('''Error: No SQL DB Name is present in settings file! Assuming "CalvinoDB"''')
        sqlName = "CalvinoDB"

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

    mqttHandler.start()

    mqttSyncEvent[0].wait(timeout = None)
    if mqttSyncEvent[1].is_set() == True:
        print("Fatal error: MQTT connection initialization error")
        quit()
    else:
        print("MQTT connection initialized")
        mqttSyncEvent[0].clear()
        mqttSyncEvent[1].clear()

        try:
            while True:
                dataProxySyncEvent.wait()
                dataProxySyncEvent.clear()
                print(dataProxyHandler.proxy)
        except KeyboardInterrupt:
            quit()

        
