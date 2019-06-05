#!/usr/bin/python3
try:
    import threading, os, inspect, signal, logging, socket, time, struct
    import re, datetime, json
    from apscheduler.schedulers.background import BackgroundScheduler
    import DataProxy, MQTT, SQL
    import encriptionHandler
except ImportError as missingImport:
    print("Critical Error: " + str(missingImport))
    quit()

socketBinded = True
safeExit = None

# This class handle the incoming connections from Middle Server.
# Every time a new connection is established, this class create and start a new Data Client istance.
class DataServerAccepter(threading.Thread):
    def __init__(self, address, port, dataProxy, dataProxyLock, dataProxySyncEvent, logger):
        self.__serverAddress = address
        self.__serverPort = port
        self.__dataProxy = dataProxy
        self.__dataProxyLock = dataProxyLock
        self.__dataProxySyncEvent = dataProxySyncEvent
        self.__serverSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
        self.__serverSocket.bind((str(self.__serverAddress), int(self.__serverPort)))
        self.__running = True
        self.__connectedClient = dict()
        self.__logger = logger
        threading.Thread.__init__(self, name = "Data Server Accepter Thread", daemon = False)

    def run(self):
        self.__serverSocket.listen(5)
        while self.__running == True:
            try:
                clientSocket, clientAddress = self.__serverSocket.accept()
            except socket.error():
                self.__logger.error("Unknown error occurred while a client tried to connect. Connection aborted")
                clientAddress = None
            
            if clientAddress != None:
                try:
                    clientThread = DataClient(address = clientAddress, clientSocket = clientSocket, dataProxy = self.__dataProxy, dataProxyLock = self.__dataProxyLock, dataProxySyncEvent = self.__dataProxySyncEvent, logger = self.__logger)
                    clientThread.start()
                    self.__connectedClient[str(clientAddress[0]) + ":" + str(clientAddress[1])] = clientThread
                    self.__logger.info("Client " + str(clientAddress[0]) + " connected")
                except Exception as reason:
                    self.__logger.error("Unhandled error occured while creating client thread for client " + str(clientAddress[0]))
                    self.__logger.info("Reason: " + str(reason))
                    clientSocket.close()
                    clientSocket = None
                    clientAddress = None
                
            self.__garbageCollector()

        self.__garbageCollector()
        self.__serverSocket.close()
        return
    
    def __garbageCollector(self):
        deathClient = []
        for client in self.__connectedClient.keys():
            if self.__connectedClient[client].__clientConnected == False:
                deathClient.append(client)
        
        for client in deathClient:
            del self.__connectedClient[client]

        return

    def stop(self):
        self.__running = False
        fakeClient = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
        fakeClient.connect(("127.0.0.1", self.__serverPort))

        for client in self.__connectedClient:
            self.__connectedClient[client].disconnect()

        fakeClient.close()
        return
         
# This class provide the comunication interface to handle the Middle Server connection.
class DataClient(threading.Thread):
    def __init__(self, address, clientSocket, dataProxy, dataProxyLock, dataProxySyncEvent, logger):
        self.__address = address
        self.__clientSocket = clientSocket
        self.__dataProxy = dataProxy
        self.__dataProxyLock = dataProxyLock
        self.__dataProxySyncEvent = dataProxySyncEvent
        self.__clientConnected = True
        self.__myPubKey = None
        self.__myPrivKey = None
        self.__hisPubKey = None
        self.__logger = logger
        threading.Thread.__init__(self, name = "Data Client " + str(address[0]), daemon = True)

    def disconnect(self):
        self.__logger.debug("Disconnesso")
        self.__clientConnected = False
        self.__clientSocket.close()
        return

    def __rsaKeyHandShake(self):
        try:
            self.__clientSocket.sendall(str("199").encode())
            answer = self.__clientSocket.recv(1024)
            if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                answer = answer.decode()
                if answer == "200":
                    (self.__myPubKey, self.__myPrivKey) = encriptionHandler.generateRSA()
                    self.__clientSocket.sendall(encriptionHandler.exportRSApub(self.__myPubKey))
                    answer = self.__clientSocket.recv(1024)
                    if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                        self.__hisPubKey = answer
                        self.__clientSocket.sendall(str("200").encode())
                        answer = self.__clientSocket.recv(1024)
                        AESkey = encriptionHandler.RSAdecrypt(privkey = self.__myPrivKey, secret = answer, skipDecoding = True)
                        if AESkey != False:
                            self.__hisPubKey = encriptionHandler.AESdecrypt(key = AESkey, secret = self.__hisPubKey, byteObject = True)
                            self.__hisPubKey = encriptionHandler.importRSApub(PEMfile = self.__hisPubKey)
                            self.__clientSocket.sendall(str("200").encode())
                            return True
                        else:
                            self.__clientSocket.sendall(str("599").encode())
        except Exception:
            pass
            
        self.__logger.warning("Error occurred while negotiating RSA keys with " + str(self.__address[0]) + " connection terminated for security reasons")
        return False
    
    def __decryptMessage(self, AESsecret, RSAsecret, byteObject = False):
        AESkey = encriptionHandler.RSAdecrypt(privkey = self.__myPrivKey, secret = RSAsecret, skipDecoding = True)
        raw = encriptionHandler.AESdecrypt(key = AESkey, secret = AESsecret, byteObject = byteObject)
        return raw

    def __generateEncryptedMessage(self, raw, byteObject = False):
        AESkey = encriptionHandler.generateAES()
        AESsecret = encriptionHandler.AESencrypt(key = AESkey, raw = raw, byteObject = byteObject)
        RSAsecret = encriptionHandler.RSAencrypt(pubkey = self.__hisPubKey, raw = AESkey)
        return (AESsecret, RSAsecret)
    
    def run(self):
        
        result = self._DataClient__rsaKeyHandShake()
        if result == False:
            self.disconnect()
        else:
            while self.__clientConnected == True:
                try:
                    request = self.getMessage(sock = self.__clientSocket)         # Get incoming request pt.1
                    if request != None and request != 0 and request != '' and request != str.encode(''):
                        RSAsecret = request                                     # First message of incoming request is the RSA secret
                        self.sendMessage(sock = self.__clientSocket, message = str("200").encode())          # Send ACK 1
                        request = self.getMessage(sock = self.__clientSocket)     #Get incoming request pt.2
                        if request != None and request != 0 and request != '' and request != str.encode(''):
                            AESsecret = request                                 # Sencond message of incoming request is the AES secret
                            self.sendMessage(sock = self.__clientSocket, message = str("200").encode())      # Send ACK2
                        else:
                            self.disconnect()
                            break
                    else:
                        self.disconnect()
                        break
                except ConnectionResetError:
                    self.disconnect()
                    break
                except ConnectionAbortedError:
                    self.disconnect()
                    break
                except ConnectionError:
                    self.disconnect()
                    break
                except Exception as test:
                    self.__logger.error("Error: Unknown comunication error occurred with client " + str(self.__address[0]))
                    self.__logger.info(str(test))
                    continue

                try:
                    request = self._DataClient__decryptMessage(AESsecret = AESsecret, RSAsecret = RSAsecret)
                    request = json.loads(request)
                except json.JSONDecodeError:
                    self.__logger.warning("Error: Received corrupted request from host " + str(self.__address[0]))
                    continue
                except Exception:
                    self.__logger.warning("Error: Received corrupted request from host " + str(self.__address[0]))
                    continue

                try:
                    if "SN" in request.keys() and "DT" in request.keys() and "FT" in request.keys() and "LT" in request.keys() and "RS" in request.keys():
                        if request["SN"] != None and request["DT"] != None and request["FT"] != None and request["LT"] != None and request["RS"] != None:

                            if request["RS"] == True:
                                safeExit.optimizeSQL(reason = True, oneTime = True, lastTime = request["LT"])

                            result = self.__dataProxy.requestData(sensorNumber = request["SN"], dataType = request["DT"], firstTime = request["FT"], lastTime = request["LT"])
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
                except Exception:
                    self.__logger.error("Error occurred while processing a request form  " + str(self.__address[0]))
                    continue

                try: 
                    resultJSON = json.dumps(result)
                    status = status.encode()
                    (resultJSON, key) = self._DataClient__generateEncryptedMessage(raw = resultJSON)
                except Exception:
                    self.__logger.error("Error occurred while encrypting an answer for " + str(self.__address[0]))
                    continue
                
                try:
                    self.sendMessage(sock = self.__clientSocket, message = key)                   # Send RSA secret
                    answer = self.getMessage(sock = self.__clientSocket)                          # Get ACK 1
                    if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                        if answer.decode() == "200":
                            self.sendMessage(sock = self.__clientSocket, message = resultJSON)    # Send AES secret
                            answer = self.getMessage(sock = self.__clientSocket)                  # Get ACK 2
                            if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                                if answer.decode() == "200":
                                    self.sendMessage(sock = self.__clientSocket, message = status)    # Send ACK 3 (status)
                                else:
                                    self.disconnect()
                                    break
                            else:
                                self.disconnect()
                                break
                        else:
                            self.disconnect()
                            break
                    else:
                        self.disconnect()
                        break
                except ConnectionResetError:
                    self.disconnect()
                    break
                except ConnectionAbortedError:
                    self.disconnect()
                    break
                except ConnectionError:
                    self.disconnect()
                    break
                except Exception:
                    continue

        
        self.__logger.info("Client " + str(self.__address[0]) + " disconnected")
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
        
# This class handle a safe server shutdown.
# This class also provide and handle the SQL optimization routine.
class shutdownHandler():
    def __init__(self, mqttHandler, dataProxyHandler, dataServerListener):
        self.mqttHandler = mqttHandler
        self.dataProxyHandler = dataProxyHandler
        self.dataServerListener = dataServerListener
        self.serverRunning = True
        self.optimizingThread = None

    def shutdown(self):
        self.serverRunning = False
        self.optimizingThread.cancel()
        self.mqttHandler.stop()
        self.dataServerListener.stop()
        self.mqttHandler.join()
        self.dataServerListener.join()
        self.optimizeSQL(reason = True, oneTime = False)
        return

    def optimizeSQL(self, reason = False, oneTime = False, lastTime = None):
        try:
            attemps = 0
            result = False
            while result == False and attemps < 3:
                attemps = attemps + 1
                if oneTime == False:
                    try:
                        firstTime = datetime.datetime.now() + datetime.timedelta(hours = int(-1))
                        lastTime = firstTime + datetime.timedelta(hours = int(1))
                        result = self.dataProxyHandler.summarizeData(firstTime = firstTime, lastTime = lastTime, skipCheck = True)
                    except Exception as motivation:
                        logging.error("Error while generating times 1 " + str(motivation))
                        raise Exception
                else:
                    try:
                        if(type(lastTime) == str):
                            groups = re.match(pattern = r"([0-9]{4})\-([0-9]{2})\-([0-9]{2})\ ([0-9]{2})\:([0-9]{2})\:([0-9]{2})", string = lastTime)
                            lastTime = datetime.datetime(year = int(groups.group(1)), month = int(groups.group(2)), day = int(groups.group(3)), hour = int(groups.group(4)), minute = int(groups.group(5)), second = int(groups.group(6)), microsecond = 123456)
                        firstTime = lastTime + datetime.timedelta(hours = int(-1))
                    except Exception as motivation:
                        logging.error("Error while manipulating times 2 " + str(motivation))
                        raise Exception

                    try:
                        result = self.dataProxyHandler.summarizeData(firstTime = firstTime, lastTime = lastTime, skipCheck = False)
                    except Exception as motivation:
                        logging.error("Error while calling summarization " + str(motivation))
                        raise Exception
            
            if reason == True:
                try:
                    firstTime = firstTime + datetime.timedelta(hours = int(1))
                    lastTime = lastTime + datetime.timedelta(hours = int(1))
                except Exception as motivation:
                    logging.error("Error while manipulating times 3 " + str(motivation))
                    raise Exception

                attemps = 0
                result = False
                while result == False and attemps < 3:
                    attemps = attemps + 1
                    try:
                        if oneTime == False:
                            result = self.dataProxyHandler.summarizeData(firstTime = firstTime, lastTime = lastTime, skipCheck = True)
                        else:
                            result = self.dataProxyHandler.summarizeData(firstTime = firstTime, lastTime = lastTime, skipCheck = False)
                    except Exception as motivation:
                        logging.error("Error while calling summarization " + str(motivation))
                        raise Exception
            
            if self.serverRunning == True and oneTime == False:
                self.optimizingThread = threading.Timer(interval = 3600, function = self.optimizeSQL)
                self.optimizingThread.start()
        except Exception:
            if self.serverRunning == True and oneTime == False:
                self.optimizingThread = threading.Timer(interval = 3600, function = self.optimizeSQL)
                self.optimizingThread.start()

# This method is called when a SIGTERM is received.
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
        safeExit = shutdownHandler(mqttHandler = mqttHandler, dataProxyHandler = dataProxyHandler, dataServerListener = dataServerListener)
        safeExit.optimizingThread = threading.Timer(interval = 3600, function = safeExit.optimizeSQL)
        safeExit.optimizingThread.start()
        signal.signal(signal.SIGTERM, sysStop)
        
        try:
            while True:
                time.sleep(100)
        except KeyboardInterrupt:
            safeExit.shutdown()
            logger.info("Server stopped because of user")
            quit()

        
