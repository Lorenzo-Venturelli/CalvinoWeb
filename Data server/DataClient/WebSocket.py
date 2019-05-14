#finire invio dati alla pagina web
import tornado.ioloop
import tornado.web
import tornado.websocket
import time
import threading
import datetime
from apscheduler.schedulers.tornado import TornadoScheduler
from tornado import gen
import DataClient

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("../Website/index.html")

class WsHandler(tornado.websocket.WebSocketHandler):
#	def open(self):
#		print("ws connected")
	def __init__(self):
		self.pastMsg = False
		self.scheduler = TornadoScheduler()
		self.sched.start()
		#self.scheduler.shutdown(wait=False)
		tornado.websocket.WebSocketHandler.__init__(self)

	def send(self, message):
		temp = self.dataRequest(message, 'temperatura')
		luce = self.dataRequest(message, 'luce')
		pressione = self.dataRequest(message, 'pressione')
		altitudine = self.dataRequest(message, 'altitudine')
		#formatta in json
		#self.write_message(<manda json>)

	def dataRequest(self, sn, dt):
		timestamp = str(datetime.datetime.now())
		timestamp = "\'" + timestamp[:-7]  + "\'"
		dict={"SN": sn ,"DT": dt,"FT": timestamp, "LT": timestamp }
		self.dataClientHandler.insertRequest(dict)
		response = self.dataClientHandler.getResponse()
		return response

	def on_message(self, message):
		if message != self.pastMsg:
			if self.pastMsg != False:
				self.scheduler.remove_job('send')
			self.pastMsg = str(message)
			self.scheduler.add_job(self.send, 'interval', seconds = 10 , id='send')
		else:
			print("No sensor number change")
			return

#    self.write_message(message)
#	def on_close(self):
#		print("ws disconnected")

class frontEndHandler(threading.Thread):
	def __init__(self, tornadoAddress, tornadoPort, dataClientHandler, syncEvent):
		self.tornadoPort = int(tornadoPort)
		self.dataClientHandler = dataClientHandler
		self.tornadoAddress = tornadoAddress
		self.syncEvent = syncEvent
		self.running = True
		threading.Thread.__init__(self, name = "Tornado thread", daemon = False)

	def run(self):
		webApp = tornado.web.Application([(r"/", MainHandler), (r"/ws", WsHandler),])
		try:
			webApp.listen(port = self.tornadoPort, address = self.tornadoAddress)
		except Exception:
			print("Fatal error: Unable to create Tornado application")
			self.stop()
			self.syncEvent.set()

		while self.running == True:
			self.syncEvent.set()
			tornado.ioloop.IOLoop.current().start()

		print("Tornado server stopped")
		return

	def stop(self):
		self.running = False
		tornado.ioloop.IOLoop.current().stop()
		return
