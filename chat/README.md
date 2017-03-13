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
python server.py PORT_NUMBER
```
<!-- ### Chat Window
Start the chat window
```
python chatWindow.py
``` -->

### Client
```
import chat

IP = '127.0.0.1'
PORT = '9000'
def guiFunc(username, message):
    print "[%s]: %s" % (username, message)

ws = chat.client.MyWSClient(username, chat.constants.PRODUCER, IP, PORT, guiFunc)
```
Here `guiFunc` is any function passed into MyWSClient which will run whenever a new message is received from the server. The function should take in a `username` and `message` as a `String`

`chat.constants.PRODUCER` is a user role that needs to be passed in when initializing a new client. The different roles are defined in `constants.py`

Now with the `ws` object you can send chat messages and files:
* `ws.chat(message)` will send a `String` message to all connected clients.
* `ws.sendFile(filepath)` takes in a `String` for a filepath and will send that file to the connected Producer.
