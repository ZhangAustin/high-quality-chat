import base64
import json
import ntpath
import os
import socket
import threading
import time

from ws4py.client.threadedclient import WebSocketClient

import constants


class ClientThread(threading.Thread):

    def __init__(self, client):
        super(ClientThread, self).__init__()
        self.client = client

    def run(self):
        print "Client Thread started"
        self.client.run_forever()


class HQCWSClient(WebSocketClient):
    def __init__(self, config, *args, **kwargs):
        """
        Starts up a chat client and hooks it up to the GUI
        :param config: A Config object to be parsed out for connection details
        """
        self.config = config
        # Get connection details from config
        chat_settings = self.config.get_section("ChatSettings")

        self.ip = chat_settings['ip_address']
        self.port = chat_settings['port']
        super(HQCWSClient, self). \
            __init__(HQCWSClient.get_ws_url(self.ip, self.port), protocols=['http-only', 'chat'], *args, **kwargs)

        self.username = chat_settings['username']
        self.role = chat_settings['role']

        self.save_directory = config.get('AudioSettings', 'recording_location')

        # Set in GUI initialization
        self.app = None
        try:
            self.connect()
        except socket.error as error:
            print "Could not connect to the server:", error
        self.client_thread = ClientThread(self)
        self.client_thread.daemon = True
        self.client_thread.start()

        # Initial settings of a client when joining
        # Defines the states of the client
        self.states = {self.username: {'mic_muted': True,
                                       'recording': False,
                                       'downloading': False,
                                       'uploading': False,
                                       # List of (filename, length) tuples
                                       "audio_files": [],
                                       # List of file names that are requested by the producers
                                       'requested_files': [],
                                       # List of(filename, length) tuples that have been downloaded.
                                       'downloaded files': []}}

    def send(self, payload, binary):
        """
        Override the default send to keep it from crashing kivy when there is no connected chat server
        :return: 
        """
        try:
            super(HQCWSClient, self).send(payload, binary)
        except socket.error:
            print "Message not sent due to socket error"
            print "Message contents: "
            print payload

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
        self.close(reason='finish() was called')

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
        message = parsed_json['message']
        if status_code == constants.SYNC_TESTSYNCMSG:
            print "Received a test sync message from {}".format(username)
        elif status_code == constants.SYNC_START_RECORDING:
            self.states[username]['recording'] = True
            print "{} started recording.".format(username)
            # Do something in GUI
            pass
        elif status_code == constants.SYNC_STOP_RECORDING:
            self.states[username]['recording'] = False
            print "{} stopped recording.".format(username)
        elif status_code == constants.SYNC_SPEAKER_ON:
            print "{} turned speakers on".format(username)
            # Do something in GUI
        elif status_code == constants.SYNC_SPEAKER_OFF:
            print "{} turned speakers off".format(username)
            # Do something in GUI
        elif status_code == constants.SYNC_REQUEST_FILE:
            filename = message['filename']
            # Update state
            if filename not in self.states[self.username]['requested_files']:
                self.states[self.username]['requested_files'].append(filename)
            # Do something in GUI
            print message['filename'] + " requested"
            if self.app:
                pass
            else:
                print "App not connected"
        elif status_code == constants.SYNC_SEND_FILE:
            filename = message['filename']
            _, file = os.path.split(filename)
            length = message['length']
            print "{} downloading {}: {} bytes".format(username, file, length)
            # Do something in GUI
            if self.app:
                self.app.update_send_files(username, message)
        elif status_code == constants.SYNC_FILE_AVAILABLE:
            filename = message['filename']
            length = message['length']
            file_tuple = (filename, length)
            self.states[username]['audio_files'].append(file_tuple)

            if self.app:
                self.app.update_available_files(username, filename, length)
            else:
                print "App not connected"
        else:
            print "Status code {} in constants.SYNC but has no handler (recv from {})".format(status_code, username)

    def send_sync(self, sync_code, **kwargs):
        """
        Forms and sends a sync message in order to reflect state changes in all connected users' GUI
        :param sync_code: Status to send, as defined in constants
        keywords:
            -filename
            -username
            -length
        """
        payload = self.new_payload()
        payload['type'] = sync_code
        if sync_code == constants.SYNC_START_RECORDING:
            self.states[self.username]['recording'] = True
            # Make an empty message
            payload['message'] = {}
            self.send(json.dumps(payload), False)

        elif sync_code == constants.SYNC_STOP_RECORDING:
            self.states[self.username]['recording'] = False
            # Make an empty message
            payload['message'] = {}
            self.send(json.dumps(payload), False)

        elif sync_code == constants.SYNC_SEND_FILE:
            # Name of the file available
            try:
                payload['message'] = {}
                payload['message']['filename'] = kwargs['filename']
                payload['message']['length'] = kwargs['length']
            except KeyError:
                print "SYNC_SENDFILE needs filename and length."
            self.send(json.dumps(payload), False)

        elif sync_code == constants.SYNC_REQUEST_FILE:
            try:
                payload['message'] = {}
                payload['message']['filename'] = kwargs['filename']
            except KeyError:
                print "SYNC_REQUEST_FILE needs username filename."
            self.send(json.dumps(payload), False)

        elif sync_code == constants.SYNC_FILE_AVAILABLE:
            try:
                _, tail = os.path.split(kwargs['filename'])
                print "Sending {} availability".format(tail)
                payload['message'] = {}
                payload['message']['filename'] = kwargs['filename']
                payload['message']['length'] = kwargs['length']
                self.send(json.dumps(payload), False)
            except KeyError:
                print "SYNC_SENDFILE needs filename and length."
            except:
                raise

        else:
            print "Uncaught sync code"
            self.send(json.dumps(payload), False)

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
        self.send(json.dumps(payload), False)
        # Avoid feedback
        time.sleep(0.2)

    def send_file(self, filepath):
        """
        Send a base64 encoded string to the server.
        :param filepath: string path to file
        :return: None
        """
        _, tail = os.path.split(filepath)
        print str(self.username) + " sending out " + str(tail)
        fh = open(filepath, 'rb')
        content = base64.b64encode(fh.read())
        payload = self.new_payload()
        payload['content'] = content
        payload['type'] = constants.FILE
        payload['filename'] = os.path.basename(filepath)
        # Send the payload as a binary message by marking binary=True
        self.send(str(json.dumps(payload)), True)
        # Avoid feedback
        time.sleep(0.2)
        fh.close()
        # self.close()

    def new_payload(self):
        """
        Make a dictionary for transmission with user details attached.
        :return: dictionary with username and role
        """
        return {"username": self.username, "role": self.role}
