#!/usr/bin/python3
import threading, os, inspect, signal, logging, socket, json, time, re
import DataClient, WebSocket

safeExit = None

class shutdownHandler():
    def __init__(self, dataClient, tornadoHandler):
        self.dataClient = dataClient
        self.tornadoHandler = tornadoHandler

    def shutdown(self):
        dataClient.disconnect()
        tornadoHandler.stop()
        return

def sysStop(signum, frame):
    safeExit.shutdown()
    quit()

if __name__ == "__main__":
    filesPath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))   # Get absolute path of files
    match = re.match(pattern = r"([A-z \/]+)(\/[A-z]+)", string = str(filesPath))
    filesPath = match.group(1) + "/Files"
    logger = logging.getLogger(name = "Middle Server")

    try:
        with open(file = filesPath + "/middleSettings.json", mode = "r") as settingsFile:
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
    try:
        loggingFile = settings["logPath"]
        if loggingFile[-1] == '/':
            loggingFile = loggingFile + "MiddleServer.log"
        else:
            loggingFile = loggingFile + "/MiddleServer.log"
        logging.basicConfig(filename = loggingFile, level = logging.INFO)
    except KeyError:
        print("Fatal Error: Logging file not found in settings. Unable to start")

    tornadoSyncEvent = threading.Event()
    dataClientSyncEvent = threading.Event()
    dataClient = DataClient.DataRequest(serverAddress = dataServerAddress, serverPort = dataServerPort, syncEvent = dataClientSyncEvent, loggingFile = loggingFile)
    dataClient.start()
    dataClientSyncEvent.wait()
    dataClientSyncEvent.clear()
    if dataClient.running == True:
        tornadoHandler = WebSocket.frontEndHandler(tornadoAddress = middleServerAddress, tornadoPort = middleServerPort, dataClientHandler = dataClient, syncEvent = tornadoSyncEvent, loggingFile = loggingFile)
        tornadoHandler.start()
        tornadoSyncEvent.wait()
        tornadoSyncEvent.clear()
        if tornadoHandler.running == True:
            safeExit = shutdownHandler(dataClient = dataClient, tornadoHandler = tornadoHandler)
            signal.signal(signal.SIGTERM, sysStop)
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                safeExit.shutdown()
                logger.info("Server stopped because of user")
                quit()
