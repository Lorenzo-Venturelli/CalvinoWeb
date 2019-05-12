#finire invio dati alla pagina web
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
		t = threading.Timer(5.0, rptsend)
		t.daemon = True
		t.start()
		temp = dataRequest(message, 'temperatura')
		luce = dataRequest(message, 'luce')
		pressione = dataRequest(message, 'pressione')
		altitudine = dataRequest(message, 'altitudine')

		self.write_message(f '{temp},{luce},{pressione},{altitudine}') # decidere come scrivere il messaggio nel miglior modo per far si che sia facilmente interpretabile da JS

	def dataRequest(self, sn, dt):
		timestamp = str(datetime.datetime.now())
		timestamp = "\'" + timestamp[:-7]  + "\'"
		dict={"SN": sn ,"DT": dt,"FT": timestamp, "LT": timestamp }
		MiddleServer.insertRequest(dict)
		response = MiddleServer.getResponse()
		return response

	def on_message(self, message):
		rptsend(self, message) #il messaggio ricevuto è numero del SN da monitorare
		'''
		from apscheduler.scheduler import Scheduler

		sched = Scheduler()
		sched.start()

		def some_job():
		    print "Every 10 seconds"

		sched.add_interval_job(some_job, seconds = 10)
		#sched.add_job(some_job, 'interval', seconds = 10)

		....
		sched.shutdown()
		'''

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
