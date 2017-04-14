import time
from chat.ChatClient import HQCWSClient
from chat import constants

from Config import Config
config = Config('conn.conf')

if __name__ == '__main__':
    try:
        client = HQCWSClient(config)

        class App:
            def update_chat(self, username, message):
                print username
                print message
                self.client.finish()

        sampleApp = App()
        sampleApp.client = client

        client.app = sampleApp

        #time.sleep(10)

        #client.finish()
    except KeyboardInterrupt:
        client.finish()
    except:
        client.finish()
