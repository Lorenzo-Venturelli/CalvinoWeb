#finire invio dati alla pagina web e sistemare il if name == main
import tornado.ioloop
import tornado.web
import tornado.websocket
import time
import threading
from tornado import gen
import DataClient

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("../Website/index.html")

class WsHandler(tornado.websocket.WebSocketHandler):
#	def open(self):
#		print("ws connected")
	def rptsend(self, message):
		threading.Timer(30.0, rptsend).start()
		temp = datarequest(message, 'temperatura')
		luce = datarequest(message, 'luce')
		pressione = datarequest(message, 'pressione')
		altitudine = datarequest(message, 'altitudine')
		self.write_message('<dati raccolti>')

	def dataRequest(self, sn, dt):
		timestamp = str(datetime.datetime.now())
		timestamp = "\'" + timestamp[:-7]  + "\'"
		dict={"SN": sn ,"DT": dt,"FT": timestamp, "LT": timestamp }
		MiddleServer.insertRequest(dict)
		response = MiddleServer.getResponse()
		return response

	def on_message(self, message):
		rptsend(self, message)

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



#    self.write_message(message)
#	def on_close(self):
#		print("ws disconnected")
'''
class ClockHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("clock.html")

class ClockWsHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		print("ws connected")

	async def on_message(self, message):
		await gen.sleep(1)
		self.write_message(u"{}".format(time.strftime('%X')))

	def on_close(self):
		print("ws disconnected")

class TemperatureHandler(tornado.web.RequestHandler):
	def get(self):
		self.render("temp.html")

class TemperatureWsHandler(tornado.websocket.WebSocketHandler):
	connections = set()

	def open(self):
		print("ws connected")
		self.connections.add(self)

	def on_message(self, message):
		print("msg received")
		for connection in self.connections:
			if connection is not self:
				connection.write_message(message)

	def on_close(self):
		print("ws disconnected")
		self.connections.remove(self)
'''