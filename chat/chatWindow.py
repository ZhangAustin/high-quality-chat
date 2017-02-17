from ws4py.client.threadedclient import WebSocketClient
import json

class MyChatClient(WebSocketClient):
    def __init__(self, *args, **kwargs):
        super(MyChatClient, self).__init__(*args, **kwargs)
    def opened(self):
        print "Connected to server"
    def closed(self, code, reason=None):
        print "Closed down", code, reason

    def received_message(self, message):
        message = str(message)
        parsed_json = json.loads(message)
        print "[%s]: %s" % (parsed_json['username'], parsed_json['message'])
    # def chat(self):
    #     message = raw_input("Message: ")
    #     payload = {"username": self.username, "message": message}
    #     self.send(json.dumps(payload), False)
    #     chat()

if __name__ == '__main__':
    try:
        ws = MyChatClient('ws://localhost:9000/', protocols=['http-only', 'chat'])
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
