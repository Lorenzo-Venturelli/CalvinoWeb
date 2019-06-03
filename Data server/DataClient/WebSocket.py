from tornado import ioloop, web, websocket, gen
import time, threading, datetime, json, logging, ast
import DataClient

serverStatus = True
negotiator = None

# This class handle incoming HTTP connections
class MainHandler(web.RequestHandler):
	def get(self):
		self.render("../Website/index.html")

# This class handle incoming WebSocket connections
class WsHandler(websocket.WebSocketHandler):
	def open(self):
		if serverStatus == True:
			self.__logger = logging.getLogger(name = "Tornado")
			self.__currentRTsensorNumber = 1
			try:	
				self.__RTscheduler = ioloop.PeriodicCallback(self.periodicRTupdate, callback_time = 15000)
				self.__RTscheduler.start()
				self.__logger.info("Client " + str(self.request.remote_ip) + " connected")
			except Exception as reason:
				self.__logger.error("Errors occurred while creating scheduler for client " + str(self.request.remote_ip))
				self.__logger.info("Reason: " + str(reason))

			self.__dataServerStatus = negotiator.negotiationStatus()

			self.__sendRTdata(sensorNumber = self.__currentRTsensorNumber)
		else:
			self.close()

	def periodicRTupdate(self):
		self.__sendRTdata(sensorNumber = self.__currentRTsensorNumber)

	def __sendRTdata(self, sensorNumber):
		dataTime = (str(datetime.datetime.now())[:-7], str(datetime.datetime.now() + datetime.timedelta(minutes = -1))[:-7])
		temp = self.__requestData(sensorNumber, 'temperatura', dataTime, False)
		light = self.__requestData(sensorNumber, 'luce', dataTime, False)
		pressure = self.__requestData(sensorNumber, 'pressione', dataTime, False)
		highness = self.__requestData(sensorNumber, 'altitudine', dataTime, False)
		try:
			temp = self.__parseRTData(data = ast.literal_eval(temp))
			light = self.__parseRTData(data = ast.literal_eval(light))
			pressure = self.__parseRTData(data = ast.literal_eval(pressure))
			highness = self.__parseRTData(data = ast.literal_eval(highness))
		except ValueError:
			rtResponse = {"type" : "service", "status" : "down"}
			self.__dataServerStatus = negotiator.negotiationStatus()

		if temp == False and light == False and pressure == False and highness == False:
			rtResponse = {"type" : "service", "status" : "down"}
			self.__dataServerStatus = negotiator.negotiationStatus()
		else:
			try:
				rtResponse = {"type" : "rtd", "temp" : temp, "light" : light, "pressure" : pressure, "highness" : highness}
				rtResponse = json.dumps(rtResponse)
			except Exception:
				return
			
		self.write_message(rtResponse)
		return

	def __sendGdata(self, sensorNumber, dataType, firstTime, lastTime):
		
		obtainedData = self.__requestData(sensorNumber = sensorNumber, dataType = dataType, dataTime = (lastTime, firstTime), reason = True)
		try:
			obtainedData = self.__parseGdata(data = ast.literal_eval(obtainedData))
		except ValueError:
			gResponse = {"type" : "service", "status" : "down"}
			self.__dataServerStatus = negotiator.negotiationStatus()

		if obtainedData == False:
			gResponse = {"type" : "service", "status" : "down"}
			self.__dataServerStatus = negotiator.negotiationStatus()
		else:
			if type(obtainedData) == dict:
				try:
					gResponse = {"type" : "gr", "values" : obtainedData, "dataType" : dataType, "sensorNumber" : sensorNumber}
					gResponse = json.dumps(gResponse)
				except Exception:
					return
			else:
				return
		
		self.write_message(gResponse)
		return
	
	def __requestData(self, sensorNumber, dataType, dataTime, reason):
		global negotiator

		request = {"SN": sensorNumber ,"DT": dataType,"FT": dataTime[1], "LT": dataTime[0], "RS" : reason}
		if negotiator.insertRequest(request) == True:
			response = negotiator.getResponse()	
			return response
		else:
			return False

	def __parseRTData(self, data):
		if type(data) == dict:
			valueNumber = 0
			value = 0
			for item in data.keys():
				value = float(value) + float(data[item][2])
				valueNumber = float(valueNumber) + 1
			if valueNumber != 0:
				value = float(value) / float(valueNumber)
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
					parsedData[data[item][1]] = round(((float(data[item][2]) + float(parsedData[data[item][1]])) / 2), 1)
				else:
					parsedData[data[item][1]] = data[item][2]
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
				message = {"type":"pong", "status":"open"}
				message = json.dumps(message)
				self.write_message(message)
				if negotiator.negotiationStatus() == True:
					self.__dataServerStatus = negotiator.negotiationStatus()
					message = {"type" : "service", "status" : "up"}
					message = json.dumps(message)
					self.write_message(message)
		else:
			parsedMessage = json.loads(message)
			if "realTimeSN" in parsedMessage.keys():
				self.__currentRTsensorNumber = int(parsedMessage["realTimeSN"])
				self.__sendRTdata(sensorNumber = self.__currentRTsensorNumber)
			elif "grapRequest" in parsedMessage.keys():
				self.__sendGdata(sensorNumber = int(parsedMessage["grapRequest"]["SN"]), 
					dataType = parsedMessage["grapRequest"]["DT"], 
					firstTime = parsedMessage["grapRequest"]["FT"], 
					lastTime = parsedMessage["grapRequest"]["LT"])
			else:
				return

	def on_close(self):
		self.__RTscheduler.stop()
		self.__logger.info("Client " + str(self.request.remote_ip) + " disconnected")

# This class provide a supervisor thread for Tornado Web Socket Server
class frontEndHandler(threading.Thread):
	def __init__(self, tornadoAddress, tornadoPort, negotiatorHandler, syncEvent, loggingFile, websitePath):
		global negotiator

		self.__tornadoPort = int(tornadoPort)
		negotiator = negotiatorHandler
		self.__tornadoAddress = tornadoAddress
		self.__syncEvent = syncEvent
		self.__running = True
		self.__ioLoop = None
		self.__websitePath = websitePath
		self.__logger = logging.getLogger(name = "Tornado")
		logging.basicConfig(filename = loggingFile, level = logging.INFO)
		threading.Thread.__init__(self, name = "Tornado thread", daemon = False)

	def run(self):
		global serverStatus

		try:
			ioLoop = ioloop.IOLoop()
			ioLoop.make_current()
			webApp = web.Application([(r"/", MainHandler), (r"/ws", WsHandler),
			(r"/assets/(.*)", web.StaticFileHandler, {"path":self.__websitePath + "/assets"}),
			(r"/images/(.*)", web.StaticFileHandler, {"path":self.__websitePath + "/images"})])
			webApp.listen(port = self.__tornadoPort, address = self.__tornadoAddress)
		except Exception as reason:
			self.__logger.critical("Unable to create Tornado application")
			self.__logger.info("Reason: " + str(reason))
			self.stop()
			self.__syncEvent.set()

		if self.__running == True:
			self.__syncEvent.set()
			try:
				self.__ioLoop = ioloop.IOLoop.instance()
				serverStatus = True
				self.__ioLoop.start()
			except Exception as reason:
				self.__logger.critical("Unable to create Tornado IO Loop")
				self.__logger.info("Reason: " + str(reason))

		self.__logger.info("Tornado server closed")
		return

	def stop(self):
		global serverStatus

		self.__running = False
		try:
			self.__ioLoop.stop()
			serverStatus = False
		except Exception as reason:
			self.__logger.error("Error occurred while stopping IO Loop")
			self.__logger.info("Reason: " + str(reason))

		return
