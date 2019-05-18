from tornado import ioloop, web, websocket, gen

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
		dataTime = (str(datetime.datetime.now())[:-7], str(datetime.datetime.now() + datetime.timedelta(minutes = -1))[:-7])
		temp = self.__requestData(sensorNumber, 'temperatura', dataTime)
		light = self.__requestData(sensorNumber, 'luce', dataTime)
		pressure = self.__requestData(sensorNumber, 'pressione', dataTime)
		highness = self.__requestData(sensorNumber, 'altitudine', dataTime)
		temp = self.__parseRTData(data = ast.literal_eval(temp))
		light = self.__parseRTData(data = ast.literal_eval(light))
		pressure = self.__parseRTData(data = ast.literal_eval(pressure))
		highness = self.__parseRTData(data = ast.literal_eval(highness))

		rtResponse = {"type" : "rtd", "temp" : temp, "light" : light, "pressure" : pressure, "highness" : highness}
		rtResponse = json.dumps(rtResponse)
		self.write_message(rtResponse)
		return

	def __sendGdata(self, sensorNumber, dataType, firstTime, lastTime):
		
		obtainedData = self.__requestData(sensorNumber = sensorNumber, dataType = dataType, dataTime = (lastTime, firstTime))
		obtainedData = self.__parseGdata(data = obtainedData)
		if type(obtainedData) == dict:
			gResponse = {"type" : "gr", "values" : obtainedData}
			gResponse = json.dumps(gResponse)
			self.write_message(gResponse)
	
	def __requestData(self, sensorNumber, dataType, dataTime):
		print(str(sensorNumber) + " " + str(dataType) + " " + str(dataTime) )
		request = {"SN": sensorNumber ,"DT": dataType,"FT": dataTime[1], "LT": dataTime[0]}
		if dataClient.insertRequest(request) == True:
			response = dataClient.getResponse()	
			return response
		else:
			return False

	def __parseRTData(self, data):
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

	def __parseGdata(self, data):
		if type(data) == dict:
			parsedData = dict()
			for item in data.keys():
				if data[item][1] in parsedData:
					parsedData[data[item][1]] = round(((data[item][2] + parsedData[data[item][1]]) / 2), 1)
				else:
					parsedData[data[item[1]]] = data[item][2]
			return parsedData
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
				self.__sendGdata(sensorNumber = int(parsedMessage["grapRequest"]["SN"]), 
					dataType = parsedMessage["grapRequest"]["DT"], 
					firstTime = parsedMessage["grapRequest"]["FT"], 
					lastTime = parsedMessage["grapRequest"]["LT"])
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
