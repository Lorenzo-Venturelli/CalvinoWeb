import socket
import json
import threading
import encriptionHandler
import queue

class DataRequest(threading.Thread):
    def __init__(self, serverAddress, serverPort, syncEvent):
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
        threading.Thread.__init__(self, name = "Data Client Thread", daemon = False)

    def disconnect(self):
        self.clientSocket.close()
        self.running = False
        self.reaquestQueue.put(False)
        return

    def __rsaHandShake(self):
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
                                    print("RSA handshake succeded")
                                    return True
        print("Fatal security error: Error occurred while negotiating RSA keys with Data Server. Connection closed for security reasons")
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
            print("Fatal error: Unable to connect to  Data Server")
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
            result = self.__executeRequest(message = message)
            if result == None:
                self.responseQueue.put(False)
            else:
                self.responseQueue.put(result)

        print("Data client disconnected")

    def __executeRequest(self, message):
        jMessage = json.dumps(message)
        (message, key) = self._DataRequest__generateEncryptedMessage(raw = jMessage, byteObject = False)
        self.clientSocket.sendall(key)
        answer = self.clientSocket.recv(1024)
        if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
            answer = answer.decode()
            if answer == "200":
                self.clientSocket.sendall(message)
                answer = self.clientSocket.recv(1024)
                if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                    answer = answer.decode()
                    if answer == "200":
                        answer = self.clientSocket.recv(1024)
                        if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                            RSAsecret = answer
                            self.clientSocket.sendall(str("200").encode())
                            answer = self.clientSocket.recv(1024)
                            if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                                AESsecret = answer
                                plainAnswer = self._DataRequest__decryptMessage(AESsecret = AESsecret, RSAsecret = RSAsecret, byteObject = False)
                                self.clientSocket.sendall(str("200").encode())
                                answer = self.clientSocket.recv(1024)
                                if answer != None and answer != 0 and answer != '' and answer != str.encode(''):
                                    if answer.decode() == "200":
                                        return(plainAnswer)
        print("Comunication error: An error occurred while comunicating with Data Server")
        return None

    def insertRequest(self, request):
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

    def getResponse(self):
        if self.running == True:
            response = self.responseQueue.get()
            return response
        else:
            return False
