import sys
import threading
from socket import *
from json import dumps, loads

# creating welcoming socket
serverPort = 12000 
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(1)
print ("The server is ready to receive")

def TCP_connection(connectionSocket, addr):
    '''
    - threads take in a function as input
    - the threads stay alive until the function ends
    - therefore, we need to create functions containing an infinite loop that does all the requried TCP functionality
    '''
    while True:
        message = connectionSocket.recv(1024)
        message = loads(message.decode())
        if message["Command"] == "message":
            connectionSocket.send(message["Payload"].encode())

        elif message["Command"] == "broadcast":
            pass

        elif message["Command"] == "whoelse":
            pass
        
        elif message["Command"] == "whoelsesince":
            pass
        
        elif message["Command"] == "block":
            pass

        elif message["Command"] == "unblock":
            pass
        
        elif message["Command"] == "logout":
            pass

def message():
    pass

def broadcast():
    pass

def whoelse():
    pass

def whoelsesince():
    pass

def block():
    pass

def unblock():
    pass

def logout():
    pass

while True:
    connectionSocket, addr = serverSocket.accept()
    thread = threading.Thread(target=TCP_connection, daemon=True, args=(connectionSocket,addr))
    thread.start()

        
   