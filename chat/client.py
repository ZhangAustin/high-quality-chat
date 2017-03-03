from ws4py.client.threadedclient import WebSocketClient
import json
import constants
import base64

class MyWSClient(WebSocketClient):
    def __init__(self, username, *args, **kwargs):
        super(MyWSClient, self).__init__(*args, **kwargs)
        self.username = username

    def opened(self):
        # self.chat()
        self.sendFile('./recordings/amy.wav')

    @staticmethod
    def closed(code, reason=None):
        print "Closed down", code, reason

    # TODO: Override received_message() to send incoming messages to gui
    def chat(self):
        message = raw_input("Message: ")
        payload = {"username": self.username, "message": message}
        payload["type"] = constants.CHAT
        self.send(json.dumps(payload), False)
        self.chat()

    def sendFile(self, filepath):
        print "Sending file"
        fh = open(filepath, 'rb')
        content = base64.b64encode(fh.read())
        payload = {}
        payload['content'] = content
        payload['type'] = constants.FILE
        payload['filename'] = fh.name
        self.send(str(json.dumps(payload)), True)
        fh.close()
        self.close()

if __name__ == '__main__':
    try:
        username = raw_input("Enter username: ")
        ws = MyWSClient(username, 'ws://127.0.0.1:9000/', protocols=['http-only', 'chat'])
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
