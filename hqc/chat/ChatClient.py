import base64
import json
import ntpath
import socket
import threading
import time
import os

from ws4py.client.threadedclient import WebSocketClient

import constants


class HQCWSClient(WebSocketClient):
    def __init__(self, config, *args, **kwargs):
        """
        Starts up a chat client and hooks it up to the GUI
        :param config: A Config object to be parsed out for connection details
        """
        self.config = config
        # Get connection details from config
        try:
            self.ip = config.get('ChatSettings', 'ip')
            self.port = config.get('ChatSettings', 'port')
        except:
            self.ip = constants.IP
            self.port = constants.PORT
        super(HQCWSClient, self).__init__(HQCWSClient.get_ws_url(self.ip, self.port),
                                          protocols=['http-only', 'chat'], *args, **kwargs)
        try:
            self.username = config.get('ChatSettings', 'username')
            self.role = config.get('ChatSettings', 'role')
            self.save_directory = config.get('AudioSettings', 'recording_location')
        except:
            self.username = constants.USERNAME
            self.role = constants.ARTIST
            self.save_directory = None
        # Set in GUI initialization
        self.app = None
        try:
            self.connect()
        except socket.error as error:
            print "Could not connect to the server:", error
        self.wst = threading.Thread(target=self.run_forever)
        self.wst.daemon = False
        self.wst.start()

    def opened(self):
        """
        Called when a connection is established
        :return: None
        """
        print "Connection opened"
        payload = self.new_payload()
        payload['type'] = constants.ROLE_VERIFICATION
        self.send(str(json.dumps(payload)), False)

    def finish(self):
        """
        Call to gracefully terminate the client from the web socket
        :return: 
        """
        self.close()
        print self.wst.is_alive
        if self.wst.is_alive:
            self.wst.join()

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

    def handle_recv_file_message(self, parsed_json):
        """
        Writes the decoded contents of a file to disk
        :param parsed_json: the original json message 
        :return: 
        """
        # Get the filename
        filename = parsed_json['filename']

        # Write the message contents to disk
        with open(self.save_directory + HQCWSClient.path_leaf(filename), 'wb') as out_file:
            out_file.write(base64.b64decode(parsed_json['content']))

        print "{} has been saved".format(filename)

    def handle_recv_chat_message(self, parsed_json):
        """
        Writes the received chat message to the GUI section
        :param parsed_json: the original json message
        :return: 
        """
        username = parsed_json['username']
        message = parsed_json['message']
        self.update_app_chat(username, message)

    def handle_recv_sync_message(self, parsed_json):
        """
        Decides type and action for a variety of sync messages, as defined in constants.py
        :param parsed_json: the original json message
        :return: 
        """
        status_code = parsed_json['type']
        username = parsed_json['username']
        if status_code == constants.SYNC_TESTSYNCMSG:
            print "Received a test sync message from {}".format(username)
        elif status_code == constants.SYNC_MICON:
            print "{} turned mic on".format(username)
            # Do something in GUI
        elif status_code == constants.SYNC_MICOFF:
            print "{} turned mic off".format(username)
            # Do something in GUI
        elif status_code == constants.SYNC_SPEAKERON:
            print "{} turned speakers on".format(username)
            # Do something in GUI
        elif status_code == constants.SYNC_SPEAKEROFF:
            print "{} turned speakers off".format(username)
            # Do something in GUI
        elif status_code == constants.SYNC_RECORDINGON:
            print "{} started recording".format(username)
            # Do something in GUI
        elif status_code == constants.SYNC_RECORDINGOFF:
            print "{} stopped recording".format(username)
            # Do something in GUI
        elif status_code == constants.SYNC_RECORDINGSTART:
            timestamp = parsed_json['message']
            print "{} started recording at {}".format(username, timestamp)
            # Do something in GUI
            pass
        elif status_code == constants.SYNC_RECORDINGSTOP:
            timestamp = parsed_json['message']
            print "{} stopped recording at {}".format(username, timestamp)
            # Do something in GUI
        else:
            print "Status code {} in constants.SYNC but has no handler (recv from {})".format(status_code, username)

    def update_app_chat(self, username, message):
        # Check if being used in our application
        if self.app is not None:
            self.app.update_chat(username, message)
        else:
            print "App is not connected"

    @staticmethod
    def print_message(username, message):
        """
        Passed into the HQCWSClient constructor and called upon receiving a message
        :param username: string username of sender
        :param message: string message of sender
        :return: None
        """
        print "[%s]: %s" % (username, message)

    def received_message(self, message):
        """
        Overrides WebSocket. Called upon receiving any message type
        :param message: JSON object of entire message
        :return: None
        """
        if self.app is not None:
            # Retrieve the message dictionary
            parsed_json = json.loads(str(message))
            # Get the message type
            message_type = parsed_json['type']

            if message_type == constants.FILE:
                self.handle_recv_file_message(parsed_json)

            elif message_type == constants.CHAT:
                self.handle_recv_chat_message(parsed_json)

            elif message_type in constants.SYNC:
                self.handle_recv_sync_message(parsed_json)

        else:
            # Retrieve the message dictionary
            parsed_json = json.loads(str(message))
            if parsed_json['type'] == constants.CHAT:
                print "[%s]: %s" % (parsed_json['username'], parsed_json['message'])

    def chat(self, message=None):
        """
        Send a chat message payload though the client socket.
        :param message: string of message to be sent
        :return: None
        """
        if not message:
            # raw_input() returns a string
            message = raw_input("Message: ")
        payload = self.new_payload()
        # Label the payload as a chat message
        payload["type"] = constants.CHAT
        # Store the message in the payload
        payload["message"] = message
        try:
            # Send the payload as a string
            self.send(json.dumps(payload), False)
        except socket.error:
            print "Message could not be sent"
        # Avoid feedback
        time.sleep(0.2)

    def send_file(self, filepath):
        """
        Send a base64 encoded string to the server.
        :param filepath: string path to file
        :return: None
        """
        fh = open(filepath, 'rb')
        content = base64.b64encode(fh.read())
        payload = self.new_payload()
        payload['content'] = content
        payload['type'] = constants.FILE
        payload['filename'] = os.path.basename(filepath)
        # Send the payload as a binary message by marking binary=True
        self.send(str(json.dumps(payload)), True)
        fh.close()
        # self.close()

    def send_sync(self, sync_code=constants.SYNC_TESTSYNCMSG, timestamp=None):
        """
        Forms and sends a sync message in order to reflect state changes in all connected users' GUI
        :param sync_code: Status to send, as defined in constants
        :param timestamp: time of HQ recording stop or start, for use with SYNC_RECORDINGSTART and SYNC_RECORDINGSTOP
        """
        payload = self.new_payload()
        payload['type'] = sync_code
        if sync_code == constants.SYNC_RECORDINGSTART or sync_code == constants.SYNC_RECORDINGSTOP:
            if timestamp is not None:
                payload['message'] = timestamp
                self.send(json.dumps(payload), False)
            else:
                print "No timestamp provided for sync message"
        else:
            self.send(json.dumps(payload), False)

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

        ws = HQCWSClient(username, constants.PRODUCER, IP, PORT, "C:Users/Boots/Desktop")
        while True:
            ws.chat()
    except KeyboardInterrupt:
        ws.close()
