import threading
import socket
import json
import DataClient

if __name__ == "__main__":
    try:
        with open(file = "./Files/middleSettings.json", mode = "r") as settingsFile:
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
    
    dataClient = DataClient.DataRequest(serverAddress = dataServerAddress, serverPort = dataServerPort)