import base64
import os
import random
import socket

import bcrypt  # dependency, pip install bcrypt


def main():
    # Do some things
    main_gui()


def main_gui():
    # Deal with the three user select screen (interested party, artist, or producer)
    user = raw_input('[[i]nterested] party, [a]rtist, [p]roducer:  ')

    if user == 'p' or user == 'producer':
        server_create()
    else:
        server_connect()


def server_connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = random.randint(1025, 65534)
    s.bind(('', port))
    conn_str = raw_input('Please enter the connection string provided by the producer:  ')
    # server = parse_conn_string(conn_str)


# def parse_conn_string(str):


def server_create():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 5432
    s.bind(('', port))

    hash = bcrypt.hashpw(os.urandom(56), bcrypt.gensalt())
    print "Please send all users the following connection string:"
    # print connection_string([ip_address, port, hash])

    handle_clients(s)


def connection_string(arr):
    string = ''
    for i in arr:
        string += i + ';'
    return base64.b64encode(string)


def handle_clients(s):
    s.listen(5)


if __name__ == '__main__':
    main()
