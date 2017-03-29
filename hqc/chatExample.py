import time
from chat import constants
from chat.ChatClient import HQCWSClient as ws_client

IP = '127.0.0.1'
PORT = '9000'
def gui_func(username, message):
    print "[%s]: %s" % (username, message)

ws = ws_client('user1' , constants.PRODUCER, IP, PORT, gui_func)
time.sleep(15)
ws.finish()
