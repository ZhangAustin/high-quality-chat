from ws4py.client.threadedclient import WebSocketClient
import json

class MyWSClient(WebSocketClient):
    def __init__(self, username, *args, **kwargs):
        super(MyWSClient, self).__init__(*args, **kwargs)
        self.username = username

    def opened(self):
        self.chat()

    @staticmethod
    def closed(code, reason=None):
        print "Closed down", code, reason

    # TODO: Override received_message() to send incoming messages to gui
    def chat(self):
        message = raw_input("Message: ")
        payload = {"username": self.username, "message": message}
        self.send(json.dumps(payload), False)
        self.chat()

if __name__ == '__main__':
    try:
        username = raw_input("Enter username: ")
        ws = MyWSClient(username, 'ws://localhost:9000/', protocols=['http-only', 'chat'])
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
