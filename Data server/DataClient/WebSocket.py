#finire invio dati alla pagina web e sistemare il if name == main
import tornado.ioloop
import tornado.web
import tornado.websocket
import time
import threading
import MiddleServer
from tornado import gen

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

      self.write_message(<dati raccolti>)

    def dataRequest(self, sn, dt):
        timestamp = str(datetime.datetime.now())
        timestamp = "\'" + timestamp[:-7]  + "\'"
        dict={"SN": sn ,"DT": dt,"FT": timestamp, "LT": timestamp }
        MiddleServer.insertRequest(dict)
        response = MiddleServer.getResponse()
        return response

	def on_message(self, message):
		rptsend(self, message)





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

def make_app():
	return tornado.web.Application([
		(r"/", MainHandler),
		(r"/ws", WsHandler),
		])

if __name__ == '__main__':
	app = make_app()
	app.listen(8888)
	print("server started at port 8888...")
	try:
		tornado.ioloop.IOLoop.current().start()
	except KeyboardInterrupt:
		print("\nserver stopped... bye")
