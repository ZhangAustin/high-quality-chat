from gevent import monkey; monkey.patch_all()
from ws4py.websocket import EchoWebSocket
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication

import json

class MyWS(EchoWebSocket):
    def received_message(self, received_message):
        print "Message received: %s" % (received_message)
        payload = {'username': 'faizan', 'message': 'Hello from planet earth'}
        self.send(json.dumps(payload), False)

server = WSGIServer(('localhost', 9000), WebSocketWSGIApplication(handler_cls=MyWS))
print "Server running on port 9000"
server.serve_forever()
