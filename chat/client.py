from ws4py.client.threadedclient import WebSocketClient
import json
import constants
import base64
import threading
import time
import datetime
import ntpath

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def getWSUrl(ip, port):
    return 'ws://' + ip + ':' + port + '/'

class MyWSClient(WebSocketClient):
    def __init__(self, username, role, ip, port, *args, **kwargs):
        super(MyWSClient, self).__init__(getWSUrl(ip, port) ,protocols=['http-only', 'chat'], *args, **kwargs)
        self.username = username
        self.role = role
        self.connect()
        wst = threading.Thread(target=self.run_forever)
        wst.daemon = False
        wst.start()

    def opened(self):
        print "Connection opened"
        payload = self.newPayload()
        payload['type'] = constants.ROLE_VERIFICATION
        self.send(str(json.dumps(payload)), False)

    @staticmethod
    def closed(code, reason=None):
        print "Closed down", code, reason

    # TODO: Override received_message() to send incoming messages to gui
    def received_message(self, message):
        message = str(message)
        parsed_json = json.loads(message)
        message_type = parsed_json['type']
        if message_type == constants.FILE:
            filename = parsed_json['filename']
            fh = open('./recordings/' + path_leaf(filename), 'wb')
            fh.write(base64.b64decode(parsed_json['content']))
            fh.close()
            print "%s has been saved" % (filename)

    def chat(self, message=None):
        if not message:
            message = raw_input("Message: ")
        payload = self.newPayload()
        payload["type"] = constants.CHAT
        payload["message"] = message
        self.send(json.dumps(payload), False)
        self.chat()

    def sendFile(self, filepath=None):
        if not filepath:
            filepath = raw_input("Insert filepath of file to send: ")
        fh = open(filepath, 'rb')
        content = base64.b64encode(fh.read())
        payload = self.newPayload()
        payload['content'] = content
        payload['type'] = constants.FILE
        payload['filename'] = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S') + '.wav'
        self.send(str(json.dumps(payload)), True)
        fh.close()
        # self.close()

    def newPayload(self):
        return {"username": self.username, "role": self.role}

if __name__ == '__main__':
    try:
        username = raw_input("Enter username: ")
        IP = '127.0.0.1'
        PORT = '9000'
        ws = MyWSClient(username, constants.PRODUCER, IP, PORT)
        ws.sendFile()
    except KeyboardInterrupt:
        ws.close()
