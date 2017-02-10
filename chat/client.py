from ws4py.client.threadedclient import WebSocketClient
import json

class MyWSClient(WebSocketClient):
    def opened(self):
        message = raw_input("Message to send to server: ")
        self.send(message, False)

    def closed(self, code, reason=None):
        print "Closed down", code, reason

    def received_message(self, message):
        message = str(message)
        parsed_json = json.loads(message)
        print "[%s]: %s" % (parsed_json['username'], parsed_json['message'])
        self.close(reason='Bye bye')

if __name__ == '__main__':
    try:
        ws = MyWSClient('ws://localhost:9000/', protocols=['http-only', 'chat'])
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
