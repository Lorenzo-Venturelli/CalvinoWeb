import threading
import socket
import time
import json
import DataProxy
import MQTT
import SQL

if __name__ == "__main__":
    mqttSyncEvent = [threading.Event(), threading.Event()]
    dataProxySyncEvent = threading.Event()
    dataProxyLock = threading.Lock()
    lastData = None

    with open(file = "./file/settings.json", mode = 'r') as settingsFile:
        settings = json.load(fp = settingsFile)

    if "brkAdr" in settings.keys():
        brkAdr = settings["brkAdr"]
    else:
        print('''Error: No broker address is present in settings file! Assuming "broker.shiftr.io"''')
        brkAdr = "broker.shiftr.io"

    if "username" in settings.keys():
        username = settings["username"]
    else:
        print('''Error: No username is present in settings file! Assuming "calvino00"''')

    if "password" in settings.keys():
        password = settings["password"]
    else:
        print('''Error: No password is present in settings file! Assuming "0123456789"''')
        password = "0123456789"

    sqlHandler = SQL.CalvinoDB(databaseAddress = brkAdr, databaseName = "CalvinoDB", user = username, password = password)
    dataProxyHandler = DataProxy.dataProxy(SQLProxy = None, syncEvents = dataProxySyncEvent, lock = dataProxyLock, proxy = lastData)
    mqttHandler = MQTT.MQTTclient(brokerAddress = brkAdr, username = username, password = password, syncEvents = mqttSyncEvent, dataProxy = dataProxyHandler)

    mqttSyncEvent[0].wait(timeout = None)
    if mqttSyncEvent[1].is_set() == True:
        print("Fatal error: MQTT connection initialization error")
        quit()
    else:
        print("MQTT connection initialized")
        
