from ws4py.client.threadedclient import WebSocketClient
import json
import constants
import base64
import threading
import time
import datetime
import ntpath


class HQCWSClient(WebSocketClient):
    def __init__(self, username, role, ip, port, gui_func, *args, **kwargs):
        super(HQCWSClient, self).__init__(HQCWSClient.get_ws_url(ip, port),
                                          protocols=['http-only', 'chat'], *args, **kwargs)
        self.username = username
        self.role = role
        self.gui_func = gui_func
        self.connect()
        wst = threading.Thread(target=self.run_forever)
        wst.daemon = False
        wst.start()

    def opened(self):
        """
        Called when a connection is established
        :return: None
        """
        print "Connection opened"
        payload = self.new_payload()
        payload['type'] = constants.ROLE_VERIFICATION
        self.send(str(json.dumps(payload)), False)

    @staticmethod
    def closed(code, reason=None):
        """
        Called when a connection is closed
        :param code: int of exit code
        :param reason: string of exit reason
        :return: None
        """
        print ("Closed down", code, reason)

    @staticmethod
    def get_ws_url(ip, port):
        """
        Gives the string representation of a connection tuple.
        :param ip: string of the IP address ex. '127.0.0.1'
        :param port: string of the port ex. '9000'
        :return: string of connection address
        """
        return 'ws://' + str(ip) + ':' + str(port) + '/'

    @staticmethod
    def path_leaf(path):
        """
        Gives the filename of a path regardless of the path format.
        :param path: string path to file
        :return: string filename
        """
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    @staticmethod
    def update_gui(username, message):
        """
        Passed into the HQCWSClient constructor and called upon receiving a message
        :param username: string username of sender
        :param message: string message of sender
        :return: None
        """
        print "[%s]: %s" % (username, message)

    def received_message(self, message):
        """
        Called upon receiving any message type
        :param message: JSON object of entire message
        :return: None
        """
        # Retrieve the message dictionary
        parsed_json = json.loads(str(message))
        # Get the message type
        message_type = parsed_json['type']

        if message_type == constants.FILE:
            # Get the filename
            filename = parsed_json['filename']

            # Write the message contents to disk
            with open('./recordings/' + HQCWSClient.path_leaf(filename), 'wb') as out_file:
                out_file.write(base64.b64decode(parsed_json['content']))

            print "{} has been saved".format(filename)

        elif message_type == constants.CHAT:
            username = parsed_json['username']
            msg = parsed_json['message']

            self.gui_func(username, msg)
        else:
            print "Message type {} not supported".format(message_type)

    def chat(self, message=None):
        """
        Send a chat message payload though the client socket.
        :param message: string of message to be sent
        :return: None
        """
        if not message:
            message = raw_input("Message: ")
        payload = self.new_payload()
        # Label the payload as a chat message
        payload["type"] = constants.CHAT
        # Store the message in the payload
        payload["message"] = message
        # Send the payload as a string
        self.send(json.dumps(payload), False)

    def send_file(self, filepath=None):
        """
        Send a base64 encoded string to the server.
        :param filepath: string path to file
        :return: None
        """
        if not filepath:
            filepath = raw_input("Insert filepath of file to send: ")
        fh = open(filepath, 'rb')
        content = base64.b64encode(fh.read())
        payload = self.new_payload()
        payload['content'] = content
        payload['type'] = constants.FILE
        payload['filename'] = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S') + '.wav'
        # Send the payload as a binary message by marking binary=True
        self.send(str(json.dumps(payload)), True)
        fh.close()
        # self.close()

    def new_payload(self):
        """
        Make a dictionary for transmission with user details attached.
        :return: dictionary with username and role
        """
        return {"username": self.username, "role": self.role}

if __name__ == '__main__':
    try:
        username = raw_input("Enter username: ")
        IP = '127.0.0.1'
        PORT = '9000'

        ws = HQCWSClient(username, constants.PRODUCER, IP, PORT, HQCWSClient.update_gui)
        ws.chat()
    except KeyboardInterrupt:
        ws.close()
