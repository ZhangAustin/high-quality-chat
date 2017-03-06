from gevent import monkey; monkey.patch_all()
from ws4py.websocket import EchoWebSocket
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication
import sys

import json
import constants
import base64
import ntpath
import time
import datetime

#from config import Config
#config = Config()

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

class MyWebsocket(EchoWebSocket):
    def opened(self):
        print dir(self)
        app = self.environ['ws4py.app']
        app.clients.append(self)
        print "%d clients connected" % (len(app.clients))
        # payload = {"type": constants.ROLE_VERIFICATION}
        # self.send(json.dumps(payload), False)

    def received_message(self, received_message):
        message_type = json.loads(str(received_message))['type']
        if message_type == constants.CHAT:
            self.handle_chat_message(received_message)
        elif message_type == constants.FILE:
            self.handle_file_transfer(received_message)
        elif message_type == constants.ROLE_VERIFICATION:
            self.handle_role_verification(received_message)

    def handle_chat_message(self, received_message):
        app = self.environ['ws4py.app']
        for client in app.clients:
            client.send(received_message, False)
        print "Sent message to %d clients" % (len(app.clients))

    def handle_file_transfer(self, received_message):
        # payload = json.loads(str(received_message))
        # filename = payload['filename']
        # fh = open('./recordings/' + path_leaf(filename), 'wb')
        # fh.write(base64.b64decode(payload['content']))
        # fh.close()
        # message = "http://localhost:5000/recordings/" + filename
        # downloadPath = {"username": "Server", "message": message}
        # downloadPath["type"] = constants.CHAT
        for client in self.environ['ws4py.app'].clients:
            if client.role == constants.PRODUCER:
                client.send(received_message, False)

    def handle_role_verification(self, received_message):
        parsed_json = json.loads(str(received_message))
        self.username = parsed_json['username']
        self.role = parsed_json['role']

    def closed(self, code, reason="A client left the room without a proper explanation."):
        app = self.environ.pop('ws4py.app')
        if self in app.clients:
            app.clients.remove(self)
        print "%d clients connected" % (len(app.clients))


class MyWebSocketApplication(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ws = WebSocketWSGIApplication(handler_cls=MyWebsocket)
        self.clients = []

    def __call__(self, environ, start_response):
        environ['ws4py.app'] = self
        return self.ws(environ, start_response)

if __name__ == '__main__':
    #IP_ADDRESS = config.get("chat_settings", "IP_ADDRESS")
    try:
        try:
            PORT = int(sys.argv[1])
        except IndexError:
            print "Port not specified"
            sys.exit(0)
        server = WSGIServer(('localhost', PORT), MyWebSocketApplication('localhost', PORT))
        print "Running server on port " + str(PORT)
        server.serve_forever()
    except KeyboardInterrupt:
        server.close()
