import time
from chat.ChatClient import HQCWSClient
from chat import constants

from Config import Config
config = Config('conn.conf')

if __name__ == '__main__':
    try:
        class App():
            def update_chat(self, username, message):
                print username
                print message

        client = HQCWSClient(config)
        client.app = App()

        time.sleep(7)

        client.chat("Hello World")

        time.sleep(5)

        client.finish()
    except:
        client.finish()
