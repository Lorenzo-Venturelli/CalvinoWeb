#riceve n-sensore (SN), data type (DT), first e last time (FT,LT), si connette, crea un json e lo invia tramite socket al data server
#2-websocket in ascolto riceve dati dal client web, e lo manda all'altra classe per poi inviarlo al data server
import socket

class DataRequest():
    def __init__(self,):
        with open(file = "./file/Request_settings.json", mode = 'r') as settingsFile:
            settings = json.load(fp = settingsFile)
        self.address = settings["address"]
        self.port = settings["port"]



    def request(self, SN, DT, FT, LT):
        message = {"SN" : SN, "DT" : DT, "FT" : FT, "LT" : LT}
        jMessage = json.dumps(message)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.address, self.port))
        s.sendall(jMessage.encode())
        recieved = ''
        while data.decode() != ''
            data = s.recv(1024)
            recieved += data  
