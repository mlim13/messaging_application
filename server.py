import sys
import threading
from socket import *
from json import dumps, loads
from database import *
from datetime import datetime
import time
from database import database

database.block_time = int(sys.argv[1])
# creating welcoming socket
serverPort = 12000 
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(1)
print ("The server is ready to receive")

def authenticated(authentication): # authentication is a user, password dict
    username = authentication["Username"]
    password = authentication["Password"]
    with open('Credentials.txt', 'r') as my_file:
        lines = my_file.readlines()
        for line in lines:
            if username == line.split()[0] and password == line.split()[1]:
                return True
    return False


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

def TCP_recv(connectionSocket, addr):
    authentication = connectionSocket.recv(1024)
    authentication = loads(authentication.decode())
    username = authentication["Username"]

    while True:  
        database.remove_blocks()  
        if database.is_username_in_credentials(username): 
            database.increment_attempt(username)
            print(database.username_attempts[username])
            if database.is_attempt_excessive(username):
                database.add_block(username)
            if username in database.username_blocked and datetime.now() < database.username_blocked[username]:
                connectionSocket.send("break".encode())
                connectionSocket.close()
                break
            if authenticated(authentication):
                database.reset_attempt(authentication["Username"])
                connectionSocket.send("proceed".encode())
                send_thread = threading.Thread(target=TCP_send, daemon=True, args=(connectionSocket,addr, authentication))
                send_thread.start()
                while True:
                    message = connectionSocket.recv(1024)
                    message = loads(message.decode())
                    if message["Command"] == "message":
                        database.messages.append(message)

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

        connectionSocket.send("again".encode())
        authentication = connectionSocket.recv(1024)
        authentication = loads(authentication.decode())
        username = authentication["Username"]        

def TCP_send(connectionSocket, addr, authentication):
    while True:
        new_messages = []
        for msg in database.messages:
            if msg["User"] == authentication["Username"]:
                connectionSocket.send((msg["Sender"] + ": " + msg["Payload"]).encode())
            else:
                new_messages.append(msg)
        database.messages = new_messages
        time.sleep(0.5)             

database.initialise_attempts()
while True:
    '''
    - we need to create a send and receive thread for EACH new TCP connection
    - this will allow sending and receiving to happen 'simultaneously' for each connection
    '''
    connectionSocket, addr = serverSocket.accept()
    recv_thread = threading.Thread(target=TCP_recv, daemon=True, args=(connectionSocket,addr))
    recv_thread.start()
