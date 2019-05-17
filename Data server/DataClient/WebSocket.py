import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
import time
import threading
import datetime
import json
from apscheduler.schedulers.tornado import TornadoScheduler
import DataClient

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("../Website/index.html")

class WsHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		try:
			self.scheduler = TornadoScheduler({'apscheduler.timezone': "Europe/Rome"})
			self.scheduler.start()
		except Exception as reason:
			print(str(reason))
		print("Connected")
		

	def send(self, message):
		temp = self.dataRequest(message, 'temperatura')
		luce = self.dataRequest(message, 'luce')
		pressione = self.dataRequest(message, 'pressione')
		altitudine = self.dataRequest(message, 'altitudine')
		message = {"temperatura" : temp, "luce" : luce, "pressione" : pressione, "altitudine" : altitudine}
		jMessage = json.dumps(message)
		self.write_message(jMessage)

	def dataRequest(self, sn, dt):
		timestamp = str(datetime.datetime.now())
		timestamp = "\'" + timestamp[:-7]  + "\'"
		dict={"SN": sn ,"DT": dt,"FT": timestamp, "LT": timestamp }
		self.dataClientHandler.insertRequest(dict)
		response = self.dataClientHandler.getResponse()
		return response

	def on_message(self, message):
		parsedMessage = json.loads(message)
		if "realTimeSN" in parsedMessage.keys():
			newSensorID = parsedMessage["realTimeSN"]
			print("RT + " + str(parsedMessage["realTimeSN"]))
		elif "grapRequest" in parsedMessage.keys():
			sensorNumber = parsedMessage["grapRequest"]["SN"]
			dataType = parsedMessage["grapRequest"]["DT"]
			firstTime = parsedMessage["grapRequest"]["FT"]
			lastTime = parsedMessage["grapRequest"]["LT"]
			print(sensorNumber + " " + dataType + " " + firstTime + " " + lastTime)
		else:
			print("No vecchio no")
			
		#if message != self.pastMsg:
			#if self.pastMsg != False:
				#self.scheduler.remove_job('send')
			#self.pastMsg = message
			#self.scheduler.add_job(self.send, trigger = 'interval', args = message, seconds = 15 , id='send')
		#else:
			#print("No sensor number change")
			#return

#    self.write_message(message)
	def on_close(self):
		print("ws disconnected")
		self.scheduler.shutdown(wait=False)

class frontEndHandler(threading.Thread):
	def __init__(self, tornadoAddress, tornadoPort, dataClientHandler, syncEvent):
		self.tornadoPort = int(tornadoPort)
		self.dataClientHandler = dataClientHandler
		self.tornadoAddress = tornadoAddress
		self.syncEvent = syncEvent
		self.running = True
		threading.Thread.__init__(self, name = "Tornado thread", daemon = False)

	def run(self):
		try:
			ioLoop = tornado.ioloop.IOLoop()
			ioLoop.make_current()
			webApp = tornado.web.Application([(r"/", MainHandler), (r"/ws", WsHandler),
			(r"/assets/(.*)", tornado.web.StaticFileHandler, {"path":"../Website/assets"}),
			(r"/images/(.*)", tornado.web.StaticFileHandler, {"path":"../Website/images"})])
			webApp.listen(port = self.tornadoPort, address = self.tornadoAddress)
		except Exception as reason:
			print("Fatal error: Unable to create Tornado application")
			print("Reason = " + str(reason))
			self.stop()
			self.syncEvent.set()

		if self.running == True:
			self.syncEvent.set()
			try:
				tornado.ioloop.IOLoop.instance().start()
			except Exception as reason:
				print("Tornado Loop start error because " + str(reason))
		else:
			print("Tornado server stopped")
			return

	def stop(self):
		self.running = False
		try:
			tornado.ioloop.IOLoop.instance().stop()
			
		except Exception as reason:
			print("Tornado Loop stop error because " + str(reason))

		return
