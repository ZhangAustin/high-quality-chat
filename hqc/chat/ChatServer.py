from gevent import monkey; monkey.patch_all()
from ws4py.websocket import EchoWebSocket
from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication
import socket
import sys
import json
import constants
import ntpath


class HQCWebSocket(EchoWebSocket):

    def opened(self):
        """
        Called when a connection is established
        :return: None
        """
        app = self.environ['ws4py.app']
        app.clients.append(self)
        print "%d clients connected" % (len(app.clients))
        # payload = {"type": constants.ROLE_VERIFICATION}
        # self.send(json.dumps(payload), False)

    @staticmethod
    def path_leaf(path):
        """
        Gives the filename of a path regardless of the path format.
        :param path: string path to file
        :return: string filename
        """
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    def received_message(self, received_message):
        """
        Decides while helper method to call for handling received messages.
        :param received_message: JSON object of received message
        :return: None
        """
        message = json.loads(str(received_message))
        message_type = message['type']
        username = message['username']
        role = message['role']

        # Keep for debugging
        if message_type in constants.SYNC_CODE_WORDS:
            print "{} from {}".format(constants.SYNC_CODE_WORDS[message_type], username)
        else:
            print "Message type: {} from {}".format(message_type, username)

        app = self.environ['ws4py.app']

        if username not in app.current_clients:
            app.current_clients[username] = {}
            app.current_clients[username]['role'] = role

            chat_message = role + " " + username + " has joined the session."
            # Send a message upon new user
            payload = {"username": "Server",
                       "type": constants.CHAT,
                       'message': chat_message}
            packed_payload = json.dumps(payload, False)
            self.handle_chat_message(packed_payload)

        if message_type == constants.CHAT:
            self.handle_chat_message(received_message)
        elif message_type == constants.FILE:
            self.handle_file_transfer(received_message)
        elif message_type == constants.ROLE_VERIFICATION:
            self.handle_role_verification(received_message)
        elif message_type in constants.SYNC:
            self.handle_sync(received_message)

    def handle_chat_message(self, received_message):
        """
        Sends a received chat message to all connected clients.
        :param received_message: JSON object of chat message
        :return: None
        """
        app = self.environ['ws4py.app']
        for client in app.clients:
            client.send(received_message, False)
        print "Sent message to %d clients" % (len(app.clients))

    def handle_file_transfer(self, received_message):
        """
        Sends a received file to all connected clients.
        :param received_message: JSON object of chat message
        :return: None
        """
        # payload = json.loads(str(received_message))
        # filename = payload['filename']
        # fh = open('./recordings/' + path_leaf(filename), 'wb')
        # fh.write(base64.b64decode(payload['content']))
        # fh.close()
        # message = "http://localhost:5000/recordings/" + filename
        # downloadPath = {"username": "Server", "message": message}
        # downloadPath["type"] = constants.CHAT
        for client in self.environ['ws4py.app'].clients:
            # Send files only to producers
            if client.role == constants.PRODUCER:
                client.send(received_message, False)

    # TODO: implement method of storing usernames and roles
    def handle_role_verification(self, received_message):
        parsed_json = json.loads(str(received_message))
        # These are almost definitely not going to be instance attribs
        self.username = parsed_json['username']
        self.role = parsed_json['role']

    def handle_sync(self, message):
        """
        Handles the distribution of sync messages.
        While identical to handle_chat_message, best to keep separated in case additional server functionality is added
        :param message: Sync message to forward
        :return: None
        """
        app = self.environ['ws4py.app']

        # Retrieve the message dictionary
        parsed_json = json.loads(str(message))
        # Get the message type
        message_type = parsed_json['type']

        producer_messages = [constants.SYNC_FILE_AVAILABLE]
        artist_messages = []
        if message_type in producer_messages:
            for client in app.clients:
                if client.role == constants.PRODUCER:
                    client.send(message, False)
        elif message_type in artist_messages:
            for client in app.clients:
                if client.role == constants.ARTIST:
                    client.send(message, False)
        # Send to everyone
        else:
            for client in app.clients:
                if client.role == constants.ARTIST:
                    client.send(message, False)

    def closed(self, code, reason="A client left the room without a proper explanation."):
        """
        Handle the removal of a client that leaves
        :param code: Status code
        :param reason: Reason given for exit
        :return: 
        """
        app = self.environ.pop('ws4py.app')
        if self in app.clients:
            app.clients.remove(self)
            # TODO: remove client from current_clients
            # if self in app.current_clients:
            #     del app.current_clients
        print "%d clients connected" % (len(app.clients))


class HQCWebSocketApplication(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ws = WebSocketWSGIApplication(handler_cls=HQCWebSocket)
        self.clients = []
        # TODO: remove clients when they exit
        self.current_clients = {}

    def __call__(self, environ, start_response):
        environ['ws4py.app'] = self
        return self.ws(environ, start_response)

if __name__ == '__main__':
    try:
        try:
            PORT = int(sys.argv[1])
        except IndexError:
            PORT = 9000
            print "Port not specified"
        server = WSGIServer(('0.0.0.0', PORT), HQCWebSocketApplication('localhost', PORT))
        print "Running server on port " + str(PORT)
        server.serve_forever()
    except KeyboardInterrupt:
        server.close()
    except socket.error:
        print "Server could not start properly. The socket may already be bound by another instance."


