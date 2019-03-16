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
        print("Error: SQL initialization error")
        print("Reason: " + str(reason))
        quit()
    dataProxyHandler = DataProxy.dataProxy(SQLProxy = sqlHandler, syncEvents = dataProxySyncEvent, lock = dataProxyLock, proxy = lastData)
    mqttHandler = MQTT.MQTTclient(brokerAddress = brkAdr, username = brkUsername, password = brkPassword, syncEvents = mqttSyncEvent, dataProxy = dataProxyHandler)

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

        
