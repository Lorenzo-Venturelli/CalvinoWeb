import threading
import socket
import json
import time
import DataClient
import WebSocket

def shutdown(dataClient, tornadoHandler):
    dataClient.disconnect()
    tornadoHandler.stop()
    return

if __name__ == "__main__":
    try:
        with open(file = "../Files/middleSettings.json", mode = "r") as settingsFile:
            settings = json.load(settingsFile)
    except FileNotFoundError:
        print("Fatal Error: Settings file not found. Unable to startup")
        quit()
    except json.JSONDecodeError:
        print("Fatal JSON: Settings file is not readable. Unable to startup")
        quit()
    except Exception:
        print("Fatal Error: Unknown error occurred while reading settings file. Unable to startup")
        quit()

    try:
        dataServerAddress = settings["dataServerAddress"]
    except KeyError:
        print("Fatal Error: Data Server Address not found. Unable to start")
        quit()
    try:
        dataServerPort = settings["dataServerPort"]
    except KeyError:
        print("Fatal Error: Data Server Port not found. Unable to start")
        quit()
    try:
        middleServerAddress = settings["middleServerAddress"]
    except KeyError:
        print("Fatal Error: Middle Server Address not found. Unable to start")
        quit()
    try:
        middleServerPort = settings["middleServerPort"]
    except KeyError:
        print("Fatal Error: Middle Server Port not found. Unable to start")
        quit()

    tornadoSyncEvent = threading.Event()
    dataClientSyncEvent = threading.Event()
    dataClient = DataClient.DataRequest(serverAddress = dataServerAddress, serverPort = dataServerPort, syncEvent = dataClientSyncEvent)
    dataClient.start()
    dataClientSyncEvent.wait()
    dataClientSyncEvent.clear()
    if dataClient.running == True:
        tornadoHandler = WebSocket.frontEndHandler(tornadoAddress = middleServerAddress, tornadoPort = middleServerPort, dataClientHandler = dataClient, syncEvent = tornadoSyncEvent)
        tornadoHandler.start()
        tornadoSyncEvent.wait()
        tornadoSyncEvent.clear()
        if tornadoHandler.running == True:
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                shutdown(dataClient = dataClient, tornadoHandler = tornadoHandler)
                print("Server stopped because of user")
                quit()
