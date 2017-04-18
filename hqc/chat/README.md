# Chat Server
Uses [wp4py](https://ws4py.readthedocs.io/en/latest/) websockets library for python 2.7

## Installation
```
pip install ws4py
pip install gevent
```


## Running It
### Server
First start the server with desired port number i.e. 9000
```
python ChatServer.py PORT_NUMBER
```

### Client
```
from chat.ChatClient import HQCWSClient
from chat import constants

from Config import Config
config = Config.get_instance('conn.conf')

if __name__ == '__main__':
    try:
        client = HQCWSClient(config)
        class App():
            def update_chat(self, username, message):
                print username
                print message
                self.client.finish()

        sampleApp = App()
        sampleApp.client = client

        client.app = sampleApp
    except:
        client.finish()
```
Here `update_chat` is any function passed into HQCWSClient which will run whenever a new message is received from the server. The function should take in a `username` and `message` as a `String`

<!-- `chat.constants.PRODUCER` is a user role that needs to be passed in when initializing a new client. The different roles are defined in `constants.py` -->

Now with the `client` object you can send chat messages and files:
* `client.chat(message)` will send a `String` message to all connected clients.
* `client.send_file(filepath)` takes in a `String` for a filepath and will send that file to the connected Producer.
