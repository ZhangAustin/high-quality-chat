import time
from chat.ChatClient import HQCWSClient
from chat import constants

from Config import Config
config = Config('conn.conf')

client = HQCWSClient(config)

time.sleep(10)

client.finish()
