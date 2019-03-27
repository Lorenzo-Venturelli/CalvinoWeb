#riceve n-sensore (SN), data type (DT), first e last time (FT,LT), si connette, crea un json e lo invia tramite socket al data server
#2-websocket in ascolto riceve dati dal client web, e lo manda all'altra classe per poi inviarlo al data server
import socket

class DataRequest():
    def __init__(self, SN, DT, FT, LT):
        self.SN = SN
        self.DT = DT
        self.FT = FT
        self.LT = LT
        with open(file = "./file/Request_settings.json", mode = 'r') as settingsFile:
            settings = json.load(fp = settingsFile)
        self.address = settings["address"]
        self.port = settings["port"]

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sok:
			sok.connect((self.address, self.port))
            self.s = sok

    def run(self):




    #def listen(self, s):
	#	data = s.recv(1024)
	#		if data.decode(encoding='UTF-8') == '':
	#	      print("Server closed connection")
	#		print("\n" + data, end='')
