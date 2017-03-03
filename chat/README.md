# Chat Server
Uses [wp4py](https://ws4py.readthedocs.io/en/latest/) websockets library for python 2.7

## Installation
```
pip install ws4py
pip install gevent
```


## Running It
### Server
First start the server
```
python server.py
```
### Chat Window
Start the chat window
```
python chatWindow.py
```

### Client
Then open multiple clients to chat with each other
```
python client.py
```

### Client from different program
```
import chat.client as hqc_client
import threading

IP = '127.0.0.1'
PORT = '9000'

ws = hqc_client.MyWSClient(username, 'ws://' + IP + ':' + PORT + '/', protocols=['http-only', 'chat'])
ws.connect()
wst = threading.Thread(target=ws.run_forever)
wst.daemon = True
wst.start()
ws.sendFile()
```
