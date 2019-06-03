import socket, json, threading, queue, logging, struct, time
import encriptionHandler

# This class handle connection with Data Server.
# This class provide a software interface to send messages and get responses.
# This class aslo implement the encrypthion background for handle comunication.
class DataRequest(threading.Thread):
    def __init__(self, serverAddress, serverPort, syncEvent, loggingFile):
        self.serverAddress = serverAddress
        self.serverPort = int(serverPort)
        self.syncEvent = syncEvent
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.myPubKey = None
        self.myPrivKey = None
        self.hisPubkey = None
        self.running = True
        self.reaquestQueue = queue.Queue()
        self.responseQueue = queue.Queue()
        self.__logger = logging.getLogger(name = "Data Client")
        logging.basicConfig(filename = loggingFile, level = logging.INFO)
        threading.Thread.__init__(self, name = "Data Client Thread", daemon = True)

    def disconnect(self):
        self.clientSocket.close()
        self.running = False
        self.reaquestQueue.put(False)
        return

    def __rsaHandShake(self):
        try:
            answer = self.clientSocket.recv(1024)
            if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                answer = answer.decode()
                if answer == "199":
                    self.clientSocket.sendall(str("200").encode())
                    answer = self.clientSocket.recv(1024)
                    if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                        self.hisPubkey = encriptionHandler.importRSApub(PEMfile = answer)
                        (self.myPubKey, self.myPrivKey) = encriptionHandler.generateRSA()
                        AESkey = encriptionHandler.generateAES()
                        AESsecret = encriptionHandler.AESencrypt(key = AESkey, raw = encriptionHandler.exportRSApub(pubkey = self.myPubKey), byteObject = True)
                        RSAsecret = encriptionHandler.RSAencrypt(pubkey = self.hisPubkey, raw = AESkey)
                        self.clientSocket.sendall(AESsecret)
                        answer = self.clientSocket.recv(1024)
                        if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                            answer = answer.decode()
                            if answer == "200":
                                self.clientSocket.sendall(RSAsecret)
                                answer = self.clientSocket.recv(1024)
                                if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                                    answer = answer.decode()
                                    if answer == "200":
                                        self.__logger.info("RSA handshake succeded")
                                        return True
        except Exception:
            pass

        self.__logger.error("Error occurred while negotiating RSA keys with Data Server. Connection closed for security reasons")
        return False

    def __generateEncryptedMessage(self, raw, byteObject = False):
        AESkey = encriptionHandler.generateAES()
        AESsecret = encriptionHandler.AESencrypt(key = AESkey, raw = raw, byteObject = byteObject)
        RSAsecret = encriptionHandler.RSAencrypt(pubkey = self.hisPubkey, raw = AESkey)
        return (AESsecret, RSAsecret)

    def __decryptMessage(self, AESsecret, RSAsecret, byteObject = False):
        AESkey = encriptionHandler.RSAdecrypt(privkey = self.myPrivKey, secret = RSAsecret, skipDecoding = True)
        raw = encriptionHandler.AESdecrypt(key = AESkey, secret = AESsecret, byteObject = byteObject)
        return raw
    
    def run(self):
        try:
            self.clientSocket.connect((self.serverAddress, self.serverPort))
        except Exception:
            self.__logger.warning("Unable to connect to Data Server")
            self.disconnect()

        if self.running == True:
            result = self._DataRequest__rsaHandShake()
            if result == False:
                self.disconnect()
        
        self.syncEvent.set()
        while self.running == True:
            message = self.reaquestQueue.get()
            if message == False:
                continue
            try:
                result = self.__executeRequest(message = message)
            except ConnectionResetError:
                self.__logger.info("Connection with Data Server has been interrupted")
                self.disconnect()
            except ConnectionAbortedError:
                self.__logger.info("Connection with Data Server has been interrupted")
                self.disconnect()
            except ConnectionError:
                self.__logger.info("Connection with Data Server has been interrupted")
                self.disconnect()
            if result == None:
                self.responseQueue.put(False)
            else:
                self.responseQueue.put(result)


        self.__logger.info("Data client disconnected")

    def __executeRequest(self, message):
        try:
            error = None
            jMessage = json.dumps(message)
            (message, key) = self._DataRequest__generateEncryptedMessage(raw = jMessage, byteObject = False)
            self.sendMessage(sock = self.clientSocket, message = key)       # Send RSA secret
            answer = self.getMessage(sock = self.clientSocket)              # Get ACK 1
            if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                answer = answer.decode()
                if answer == "200":
                    self.sendMessage(sock = self.clientSocket, message = message)       # Send AES secret
                    answer = self.getMessage(sock = self.clientSocket)                  # Get ACK 2
                    if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                        answer = answer.decode()
                        if answer == "200":
                            answer = self.getMessage(sock = self.clientSocket)          # Get response pt.1
                            if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                                RSAsecret = answer                                      # First response message is RSA secret
                                self.sendMessage(sock = self.clientSocket, message = str("200").encode())          # Send ACK 1
                                answer = self.getMessage(sock = self.clientSocket)      # Get response pt.2
                                if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                                    AESsecret = answer                                  # Sencond response message is AES secret
                                    plainAnswer = self._DataRequest__decryptMessage(AESsecret = AESsecret, RSAsecret = RSAsecret, byteObject = False)
                                    self.sendMessage(sock = self.clientSocket, message = str("200").encode())      # Send ACK 2
                                    answer = self.getMessage(sock = self.clientSocket)  # Get ACK 3 (Status)
                                    if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                                        if answer.decode() == "200":
                                            return(plainAnswer)
                                        else:
                                            error = "Failed ACK 3 - Got " + str(answer.decode())
                                    else:
                                        error = "Failed ACK 3 - Got anything"
                                else:
                                    error = "Failed reciving AES secret"
                            else:
                                error = "Failed reciving RSA secret"
                        else:
                            error = "Failed ACK 2 - Got " + str(answer)
                    else:
                        error = "Failed ACK 2 - Got anything"
                else:
                    error = "Failed ACK 1 - Got " + str(answer)
            else:
                error = "Failed ACK 1 - Got anything"

            self.__logger.warning("An error occurred while comunicating with Data Server")
            self.__logger.info("Reason: " + error)
            return None
        except ConnectionResetError:
            raise ConnectionResetError
        except ConnectionAbortedError:
            raise ConnectionAbortedError
        except ConnectionError:
            raise ConnectionError
        except Exception:
            return None

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
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(sock, msglen)
    
    def recvall(self, sock, n):
        try:
        # Helper function to recv n bytes or return None if EOF is hit
            data = b''
            while len(data) < n:
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

    def insertRequest(self, request):
        try:
            if self.running == True:
                if type(request) is dict:
                    keys = request.keys()
                    if "SN" in keys and "DT" in keys and "FT" in keys and "LT" in keys:
                        self.reaquestQueue.put(request)
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        except Exception:
            return False

    def getResponse(self):
        try:
            if self.running == True:
                response = self.responseQueue.get()
                return response
            else:
                return False
        except Exception:
            return False

# This class handle connections and disconnections with Data Server
# A connection attempt is done every minute until a connection is established.
# This class also provide a software interface to allow other threads to talk with Data Server.
# A new istance of Data Client is istanciated when the connection is established.
class connectionNegotiator(threading.Thread):
    def __init__(self, serverAddress, serverPort, loggingFile):
        self.__serverAddress = serverAddress
        self.__serverPort = serverPort
        self.__syncEvent = threading.Event()
        self.__negotiationEvent = threading.Event()
        self.__loggingFile = loggingFile
        self.__logger = logging.getLogger(name = "Negotiator")
        logging.basicConfig(filename = self.__loggingFile, level = logging.DEBUG)
        self.__keepRunning = True
        self.__connectionNegotiated = False
        self.__DataClient = None
        threading.Thread.__init__(self, name = "Negotiator", daemon = False)

    def shutdown(self):
        self.__keepRunning = False
        if self.__connectionNegotiated == True:
            self.__DataClient.disconnect()
        return

    def insertRequest(self, request):
        if self.__connectionNegotiated == True:
            return self.__DataClient.insertRequest(request = request)
        else:
            return False

    def getResponse(self):
        if self.__connectionNegotiated == True:
            return self.__DataClient.getResponse()
        else:
            return False

    def negotiationStatus(self):
        return self.__connectionNegotiated

    def waitNegotiation(self):
        self.__negotiationEvent.wait()
        return

    def run(self):
        while self.__keepRunning == True:
            try:
                self.__DataClient = DataRequest(serverAddress = self.__serverAddress, serverPort = self.__serverPort, syncEvent = self.__syncEvent, loggingFile = self.__loggingFile)
                self.__DataClient.start()
                self.__syncEvent.wait()
                self.__syncEvent.clear()
                if self.__DataClient.running == True:
                    self.__connectionNegotiated = True
                    self.__negotiationEvent.set()
                    self.__logger.info("Connection negotiatied with Data Server")
                    self.__DataClient.join()
                    self.__logger.info("Connection interrupted with Data Server")
                    self.__DataClient = None
                    self.__connectionNegotiated = False
                    self.__negotiationEvent.clear()
                else:
                    self.__DataClient = None
                    self.__connectionNegotiated = False
                    self.__negotiationEvent.clear()
                    time.sleep(60)
            except Exception:
                continue
