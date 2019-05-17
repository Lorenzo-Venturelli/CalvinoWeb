from tornado import ioloop, web, websocket, gen
from apscheduler.schedulers.tornado import TornadoScheduler
import time, threading, datetime, json, logging, ast
import DataClient

serverStatus = True
dataClient = None

class MainHandler(web.RequestHandler):
	def get(self):
		self.render("../Website/index.html")

class WsHandler(websocket.WebSocketHandler):
	def open(self):
		self.__logger = logging.getLogger(name = "Tornado")
		self.currentRTsensorNumber = 1
		try:	
			self.RTscheduler = ioloop.PeriodicCallback(self.periodicRTupdate, callback_time = 15000)
			self.RTscheduler.start()
			self.__logger.info("Client " + str(self.request.remote_ip) + " connected")
		except Exception as reason:
			self.__logger.error("Errors occurred while creating scheduler for client " + str(self.request.remote_ip))
			self.__logger.info("Reason: " + str(reason))

		self.sendRTdata(sensorNumber = self.currentRTsensorNumber)


	def periodicRTupdate(self):
		self.sendRTdata(sensorNumber = self.currentRTsensorNumber)

	def sendRTdata(self, sensorNumber):
		print(sensorNumber)
		dataTime = (str(datetime.datetime.now())[:-7], str(datetime.datetime.now() + datetime.timedelta(minutes = -1))[:-7])
		temp = self.requestRTdata(sensorNumber, 'temperatura', dataTime)
		light = self.requestRTdata(sensorNumber, 'luce', dataTime)
		pressure = self.requestRTdata(sensorNumber, 'pressione', dataTime)
		highness = self.requestRTdata(sensorNumber, 'altitudine', dataTime)
		temp = self.__parseData(data = ast.literal_eval(temp))
		light = self.__parseData(data = ast.literal_eval(light))
		pressure = self.__parseData(data = ast.literal_eval(pressure))
		highness = self.__parseData(data = ast.literal_eval(highness))

		rtResponse = {"type" : "rtd", "temp" : temp, "light" : light, "pressure" : pressure, "highness" : highness}
		print(rtResponse)
		rtResponse = json.dumps(rtResponse)
		self.write_message(rtResponse)
		print(str({"type" : "rtd", "temp" : temp, "light" : light, "pressure" : pressure, "highness" : highness}))
		return

	def requestRTdata(self, sensorNumber, dataType, dataTime):
		request = {"SN": sensorNumber ,"DT": dataType,"FT": dataTime[1], "LT": dataTime[0]}
		if dataClient.insertRequest(request) == True:
			response = dataClient.getResponse()	
			return response
		else:
			return False

	def __parseData(self, data):
		if type(data) == dict:
			valueNumber = 0
			value = 0
			for item in data.keys():
				value = value + float(data[item][2])
				valueNumber = valueNumber + 1
			if valueNumber != 0:
				value = value / valueNumber
				return round(value, 1)
			else:
				return False
		else:
			return False

	def on_message(self, message):
		global serverStatus

		if message == "ping":
			if serverStatus == False:
				message = {"type":"pong", "status":"close"}
				message = json.dumps(message)
				self.write_message(message)
			else:
				message = message = {"type":"pong", "status":"open"}
				message = json.dumps(message)
				self.write_message(message)
		else:
			parsedMessage = json.loads(message)
			if "realTimeSN" in parsedMessage.keys():
				self.currentRTsensorNumber = int(parsedMessage["realTimeSN"])
				self.sendRTdata(sensorNumber = self.currentRTsensorNumber)
			elif "grapRequest" in parsedMessage.keys():
				sensorNumber = parsedMessage["grapRequest"]["SN"]
				dataType = parsedMessage["grapRequest"]["DT"]
				firstTime = parsedMessage["grapRequest"]["FT"]
				lastTime = parsedMessage["grapRequest"]["LT"]
			else:
				print("No vecchio no")

	def on_close(self):
		self.RTscheduler.stop()
		self.__logger.info("Client " + str(self.request.remote_ip) + " disconnected")

class frontEndHandler(threading.Thread):
	def __init__(self, tornadoAddress, tornadoPort, dataClientHandler, syncEvent, loggingFile):
		global dataClient

		self.tornadoPort = int(tornadoPort)
		dataClient = dataClientHandler
		self.tornadoAddress = tornadoAddress
		self.syncEvent = syncEvent
		self.running = True
		self.ioLoop = None
		self.__logger = logging.getLogger(name = "Tornado")
		logging.basicConfig(filename = loggingFile, level = logging.INFO)
		threading.Thread.__init__(self, name = "Tornado thread", daemon = False)

	def run(self):
		global serverStatus

		try:
			ioLoop = ioloop.IOLoop()
			ioLoop.make_current()
			webApp = web.Application([(r"/", MainHandler), (r"/ws", WsHandler),
			(r"/assets/(.*)", web.StaticFileHandler, {"path":"../Website/assets"}),
			(r"/images/(.*)", web.StaticFileHandler, {"path":"../Website/images"})])
			webApp.listen(port = self.tornadoPort, address = self.tornadoAddress)
		except Exception as reason:
			self.__logger.critical("Unable to create Tornado application")
			self.__logger.info("Reason: " + str(reason))
			self.stop()
			self.syncEvent.set()

		if self.running == True:
			self.syncEvent.set()
			try:
				self.ioLoop = ioloop.IOLoop.instance()
				serverStatus = True
				self.ioLoop.start()
				self.ioLoop.close()
			except Exception as reason:
				self.__logger.critical("Unable to create Tornado IO Loop")
				self.__logger.info("Reason: " + str(reason))

		self.__logger.info("Tornado server closed")
		return

	def stop(self):
		global serverStatus

		self.running = False
		try:
			self.ioLoop.stop()
			serverStatus = False
		except Exception as reason:
			self.__logger.error("Error occurred while stopping IO Loop")
			self.__logger.info("Reason: " + str(reason))

		return
