from gevent import monkey; monkey.patch_all()
from ws4py.websocket import EchoWebSocket
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication

import json


class MyWebsocket(EchoWebSocket):
    def opened(self):
        app = self.environ['ws4py.app']
        app.clients.append(self)
        print "%d clients connected" % (len(app.clients))

    def received_message(self, received_message):
        print received_message
        app = self.environ['ws4py.app']
        for client in app.clients:
            client.send(received_message, False)
        print "Sent message to %d clients"

    def closed(self, code, reason="A client left the room without a proper explanation."):
        app = self.environ.pop('ws4py.app')
        if self in app.clients:
            app.clients.remove(self)


class MyWebSocketApplication(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ws = WebSocketWSGIApplication(handler_cls=MyWebsocket)
        self.clients = []

    def __call__(self, environ, start_response):
        environ['ws4py.app'] = self
        return self.ws(environ, start_response)

server = WSGIServer(('localhost', 9000), MyWebSocketApplication('localhost', 9000))
print "Running server on port 9000"
server.serve_forever()
