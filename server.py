import sys
import threading
from socket import *
from json import dumps, loads
from database import *
import time

# creating welcoming socket
serverPort = 12000 
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(1)
print ("The server is ready to receive")

# list of message dictionaries
# we currently don't have a means of accessing individual threads (and in turn sockets) at will. We don't have any means of identifying which thread is which. Thus, we can easily send messages from client to server, but we will have trouble sending messages on from server to a specific client
# we can use a global store of our data/messages to (perhaps naively) solve this
# when the scheduler gets round to dealing with the receiving client's thread, it will grab the message from global store and send it on
messages = []

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

def TCP_recv(connectionSocket, addr, authentication):
    '''
    - threads take in a function as input
    - the threads stay alive until the function ends
    - therefore, we need to create functions containing an infinite loop that does all the requried TCP functionality
    '''
    global messages
    while True:
        message = connectionSocket.recv(1024)
        message = loads(message.decode())
        if message["Command"] == "message":
            messages.append(message)

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
        
        time.sleep(0.5)

def TCP_send(connectionSocket, addr, authentication):
    global messages
    while True:
        print(messages)
        new_messages = []
        # first we deal with any messages that need to be send to THIS socket
        for msg in messages:
            #print("0")
            #print(authentication)
            if msg["User"] == authentication["Username"]:
                #print("1")
                #connectionSocket.send(">".encode())
                connectionSocket.send((msg["Sender"] + ": " + msg["Payload"]).encode())
                # print("SEND \n")
            else:
                new_messages.append(msg)
        #print("3")
        #print(messages)
        messages = new_messages
        # print(messages)
        time.sleep(0.5)
                

while True:
    connectionSocket, addr = serverSocket.accept()
    authentication = connectionSocket.recv(1024)
    authentication = loads(authentication.decode())
    recv_thread = threading.Thread(target=TCP_recv, daemon=True, args=(connectionSocket,addr,authentication))
    send_thread = threading.Thread(target=TCP_send, daemon=True, args=(connectionSocket,addr,authentication))
    recv_thread.start()
    send_thread.start()

        
   