#!/usr/bin/python3
import threading, os, inspect, signal, logging, socket, time, struct
import re, datetime, json
from apscheduler.schedulers.background import BackgroundScheduler
import DataProxy, MQTT, SQL
import encriptionHandler

startingTime = datetime.datetime.now()
startingTime = startingTime.astimezone()
socketBinded = True
safeExit = None

class DataServerAccepter(threading.Thread):
    def __init__(self, address, port, dataProxy, dataProxyLock, dataProxySyncEvent, logger):
        self.serverAddress = address
        self.serverPort = port
        self.dataProxy = dataProxy
        self.dataProxyLock = dataProxyLock
        self.dataProxySyncEvent = dataProxySyncEvent
        self.serverSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
        self.serverSocket.bind((str(self.serverAddress), int(self.serverPort)))
        self.__running = True
        self.connectedClient = dict()
        self.logger = logger
        threading.Thread.__init__(self, name = "Data Server Accepter Thread", daemon = False)

    def run(self):
        self.serverSocket.listen(5)
        while self.__running == True:
            try:
                clientSocket, clientAddress = self.serverSocket.accept()
            except socket.error():
                self.logger.error("Unknown error occurred while a client tried to connect. Connection aborted")
                clientAddress = None
            
            if clientAddress != None:
                try:
                    clientThread = DataClient(address = clientAddress, clientSocket = clientSocket, dataProxy = self.dataProxy, dataProxyLock = self.dataProxyLock, dataProxySyncEvent = self.dataProxySyncEvent, logger = self.logger)
                    clientThread.start()
                    self.connectedClient[str(clientAddress[0])] = clientThread
                    self.logger.info("Client " + str(clientAddress[0]) + " connected")
                except Exception as reason:
                    self.logger.error("Unhandled error occured while creating client thread for client " + str(clientAddress[0]))
                    self.logger.info("Reason: " + str(reason))
                    clientSocket.close()
                    clientSocket = None
                    clientAddress = None
                
            self.__garbageCollector()

        self.__garbageCollector()
        self.serverSocket.close()
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
    def __init__(self, address, clientSocket, dataProxy, dataProxyLock, dataProxySyncEvent, logger):
        self.address = address
        self.clientSocket = clientSocket
        self.dataProxy = dataProxy
        self.dataProxyLock = dataProxyLock
        self.dataProxySyncEvent = dataProxySyncEvent
        self.clientConnected = True
        self.myPubKey = None
        self.myPrivKey = None
        self.hisPubKey = None
        self.logger = logger
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
                self.clientSocket.sendall(encriptionHandler.exportRSApub(self.myPubKey))
                answer = self.clientSocket.recv(1024)
                if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                    self.hisPubKey = answer
                    self.clientSocket.sendall(str("200").encode())
                    answer = self.clientSocket.recv(1024)
                    AESkey = encriptionHandler.RSAdecrypt(privkey = self.myPrivKey, secret = answer, skipDecoding = True)
                    if AESkey != False:
                        self.hisPubKey = encriptionHandler.AESdecrypt(key = AESkey, secret = self.hisPubKey, byteObject = True)
                        self.hisPubKey = encriptionHandler.importRSApub(PEMfile = self.hisPubKey)
                        self.clientSocket.sendall(str("200").encode())
                        return True
                    else:
                        self.clientSocket.sendall(str("599").encode())
        self.logger.warning("Error occurred while negotiating RSA keys with " + str(self.address[0]) + " connection terminated for security reasons")
        return False
    
    def __decryptMessage(self, AESsecret, RSAsecret, byteObject = False):
        AESkey = encriptionHandler.RSAdecrypt(privkey = self.myPrivKey, secret = RSAsecret, skipDecoding = True)
        raw = encriptionHandler.AESdecrypt(key = AESkey, secret = AESsecret, byteObject = byteObject)
        return raw

    def __generateEncryptedMessage(self, raw, byteObject = False):
        AESkey = encriptionHandler.generateAES()
        AESsecret = encriptionHandler.AESencrypt(key = AESkey, raw = raw, byteObject = byteObject)
        RSAsecret = encriptionHandler.RSAencrypt(pubkey = self.hisPubKey, raw = AESkey)
        return (AESsecret, RSAsecret)
    
    def run(self):
        if self.address[0] == "127.0.0.1":
            self.disconnect()
            return

        result = self._DataClient__rsaKeyHandShake()
        if result == False:
            self.disconnect()
        else:
            while self.clientConnected == True:
                try:
                    request = self.getMessage(sock = self.clientSocket)         # Get incoming request pt.1
                    if request != None and request != 0 and request != '' and request != str.encode(''):
                        RSAsecret = request                                     # First message of incoming request is the RSA secret
                        self.sendMessage(sock = self.clientSocket, message = str("200").encode())          # Send ACK 1
                        request = self.getMessage(sock = self.clientSocket)     #Get incoming request pt.2
                        if request != None and request != 0 and request != '' and request != str.encode(''):
                            AESsecret = request                                 # Sencond message of incoming request is the AES secret
                            self.sendMessage(sock = self.clientSocket, message = str("200").encode())      # Send ACK2
                        else:
                            self.disconnect()
                            continue
                    else:
                        self.disconnect()
                        continue
                except ConnectionResetError:
                    self.clientSocket.disconnect()
                    continue
                except ConnectionAbortedError:
                    self.clientSocket.disconnect()
                    continue
                except ConnectionError:
                    self.clientSocket.disconnect()
                    continue
                except Exception as test:
                    self.logger.error("Error: Unknown comunication error occurred with client " + str(self.address[0]))
                    self.logger.info(str(test))
                    continue

                request = self._DataClient__decryptMessage(AESsecret = AESsecret, RSAsecret = RSAsecret)
                try:
                    request = json.loads(request)
                except json.JSONDecodeError:
                    self.logger.warning("Error: Received corrupted request from host " + str(self.address[0]))
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
                status = status.encode()
                (resultJSON, key) = self._DataClient__generateEncryptedMessage(raw = resultJSON)
                
                try:
                    self.sendMessage(sock = self.clientSocket, message = key)                   # Send RSA secret
                    answer = self.getMessage(sock = self.clientSocket)                          # Get ACK 1
                    if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                        if answer.decode() == "200":
                            self.sendMessage(sock = self.clientSocket, message = resultJSON)    # Send AES secret
                            answer = self.getMessage(sock = self.clientSocket)                  # Get ACK 2
                            if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                                if answer.decode() == "200":
                                    self.sendMessage(sock = self.clientSocket, message = status)    # Send ACK 3 (status)
                                else:
                                    self.disconnect()
                                    continue
                            else:
                                self.disconnect()
                                continue
                        else:
                            self.disconnect()
                            continue
                    else:
                        self.disconnect()
                        continue
                except ConnectionResetError:
                    self.clientSocket.disconnect()
                    continue
                except ConnectionAbortedError:
                    self.clientSocket.disconnect()
                    continue
                except ConnectionError:
                    self.clientSocket.disconnect()
                    continue
                except Exception:
                    self.logger.warning("Error: Unknown comunication error occurred with client " + str(self.address[0]))
                    continue
        
        self.logger.info("Client " + str(self.address[0]) + " disconnected")
        return
    
    def sendMessage(self, sock, message):
        message = struct.pack('>I', len(message)) + message
        try:
            sock.sendall(message)
        except ConnectionResetError:
            raise ConnectionResetError
        except ConnectionAbortedError:
            raise ConnectionAbortedError
        except ConnectionError:
            raise ConnectionError
        except Exception:
            return False
        return True

    def getMessage(self, sock):
        try:
            # Read message length and unpack it into an integer
            raw_msglen = self.recvall(sock, 4)
            if not raw_msglen:
                return None
            msglen = struct.unpack('>I', raw_msglen)[0]
            # Read the message data
            return self.recvall(sock, msglen)
        except ConnectionResetError:
            raise ConnectionResetError
        except ConnectionAbortedError:
            raise ConnectionAbortedError
        except ConnectionError:
            raise ConnectionError
    
    def recvall(self, sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            try:
                packet = sock.recv(n - len(data))
                if not packet:
                    return None
                data += packet
            except ConnectionResetError:
                raise ConnectionResetError
            except ConnectionAbortedError:
                raise ConnectionAbortedError
            except ConnectionError:
                raise ConnectionError
        return data   
        

class shutdownHandler():
    def __init__(self, mqttHandler, dataProxyHandler, dataServerListener, startingTime):
        self.mqttHandler = mqttHandler
        self.dataProxyHandler = dataProxyHandler
        self.dataServerListener = dataServerListener
        self.startingTime = startingTime

    def shutdown(self):
        self.mqttHandler.stop()
        self.dataServerListener.stop()
        self.mqttHandler.join()
        self.dataServerListener.join()
        optimizeSQL(dataProxy = dataProxyHandler, reason = True)
        return

def optimizeSQL(dataProxy, reason):
    firstTime = datetime.datetime.now() + datetime.timedelta(hours = -1)
    lastTime = firstTime + datetime.timedelta(hours = +1)
    dataProxy.summarizeData(firstTime = firstTime, lastTime = lastTime, skipCheck = False)
    if reason == True:
        firstTime = firstTime + datetime.timedelta(hours = +1)
        lastTime = lastTime + datetime.timedelta(hours = +1)
        dataProxy.summarizeData(firstTime = firstTime, lastTime = lastTime, skipCheck = False)

def sysStop(signum, frame):
    safeExit.shutdown()
    quit()

if __name__ == "__main__":
    mqttSyncEvent = [threading.Event(), threading.Event()]
    dataProxySyncEvent = threading.Event()
    dataProxyLock = threading.Lock()
    lastData = None
    logger = logging.getLogger(name = "DataServer")
    filesPath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))   # Get absolute path of files
    match = re.match(pattern = r"([A-z \/]+)(\/[A-z]+)", string = str(filesPath))
    filesPath = match.group(1) + "/Files"

    try:
        with open(file = filesPath + "/settings.json", mode = 'r') as settingsFile:
            settings = json.load(fp = settingsFile)
    except FileNotFoundError:
        print("Critical Error: Settings file not found")
        settings = dict()
    except json.JSONDecodeError:
        print("Critical Error: Settings file has an invalid format")
        settings = dict()
    except Exception:
        print("Critical Error: An unknown error occurred while reading the settings file")
        settings = dict()

    if "brkAdr" in settings.keys():
        brkAdr = settings["brkAdr"]
    else:
        print("Critical Error: No broker address is present in settings file")
        quit()

    if "brkUsername" in settings.keys():
        brkUsername = settings["brkUsername"]
    else:
        print("Critical Error: No broker username is present in settings file!")
        quit()

    if "brkPassword" in settings.keys():
        brkPassword = settings["brkPassword"]
    else:
        print("Critical Error: No broker password is present in settings file")
        quit()

    if "sqlAdr" in settings.keys():
        sqlAdr = settings["sqlAdr"]
    else:
        print("Critical Error: No SQL Server address is present in settings file")
        quit()

    if "sqlUsername" in settings.keys():
        sqlUsername = settings["sqlUsername"]
    else:
        print("Critical Error: No SQL username is present in settings file!")
        quit()

    if "sqlPassword" in settings.keys():
        sqlPassword = settings["sqlPassword"]
    else:
        print("Critical Error: No SQL password is present in settings file!")
        quit()

    if "sqlName" in settings.keys():
        sqlName = settings["sqlName"]
    else:
        print("Critical Error: No SQL DB Name is present in settings file!")
        quit()

    if "logPath" in settings.keys():
        loggingFile = settings["logPath"]
        if loggingFile[-1] == '/':
            loggingFile = loggingFile + "DataServer.log"
        else:
            loggingFile = loggingFile + "/DataServer.log"
        logging.basicConfig(filename = loggingFile, level = logging.INFO)
    else:
        print("Critical Error: No Log Path is provided by settings file! Unable to start")
        quit()

    try:
        sqlHandler = SQL.CalvinoDB(databaseAddress = sqlAdr, databaseName = sqlName, user = sqlUsername, password = sqlPassword, loggingFile = loggingFile)
    except Exception as reason:
        logger.critical("SQL initialization error. Reason = " + str(reason))
        quit()

    try:
        dataProxyHandler = DataProxy.dataProxy(SQLProxy = sqlHandler, syncEvents = dataProxySyncEvent, lock = dataProxyLock, proxy = lastData, loggingFile = loggingFile)
    except Exception as reason:
        logger.critical("Data Proxy initialization error. Reason = " + str(reason))
        quit()
    
    try:
        mqttHandler = MQTT.MQTTclient(brokerAddress = brkAdr, username = brkUsername, password = brkPassword, syncEvents = mqttSyncEvent, dataProxy = dataProxyHandler, loggingFile = loggingFile)
    except Exception as reason:
        logger.critical("MQTT initialization error. Reason = " + str(reason))
        quit()

    try:
        dataServerListener = DataServerAccepter(address = '', port = 2000, dataProxy = dataProxyHandler, dataProxyLock = dataProxyLock, dataProxySyncEvent = dataProxySyncEvent, logger = logger)
    except Exception as reason:
        logger.critical("Data Server can not be started. Reason = " + str(reason))
        quit()

    mqttHandler.start()

    mqttSyncEvent[0].wait(timeout = None)
    if mqttSyncEvent[1].is_set() == True:
        logger.critical("MQTT connection initialization error")
        logger.info("Server stopped because fatal MQTT connection error")
        dataServerListener.stop()
        quit()
    else:
        logger.info("MQTT connection initialized")
        mqttSyncEvent[0].clear()
        mqttSyncEvent[1].clear()
        dataServerListener.start()
        safeExit = shutdownHandler(mqttHandler = mqttHandler, dataProxyHandler = dataProxyHandler, dataServerListener = dataServerListener, startingTime = startingTime)
        signal.signal(signal.SIGTERM, sysStop)
        scheduler = BackgroundScheduler()
        scheduler.start()
        optimizingJob = scheduler.add_job(optimizeSQL, "interval", (dataProxyHandler, False), "OpzJob", "Optimize SQL routine", seconds = 5)
        print(optimizingJob)

        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            safeExit.shutdown()
            logger.info("Server stopped because of user")
            quit()

        
