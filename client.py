from socket import *
from json import dumps
import sys
import threading
import time

# defining the (known) server parameters
serverName = 'localhost'
serverPort = 12000

def string_to_message(input_string, sender):
    '''
    From an inputted string ('message'), we want to return a dictionary indexed by all the required fields:
        - command
        - User
            this will be used by the Server to determine the dest IP and dest port
        - payload (either time or the message to be sent)
    '''
    # initialising message fields to be empty
    command = ""
    user = ""
    payload = ""

    input_list = input_string.split(" ", 2)
    command = input_list[0]
    if command == "message":
        user = input_list[1]
        payload = input_list[2]
    elif command == "broadcast" or command == "whoelsesince":
        payload = input_list[1]
    elif command == "block" or command == "unblock":
        user = input_list[1]

    message = {
        "Command": command,
        "User": user,
        "Payload": payload,
        "Sender": sender
    }

    return message
    
def send_func(clientSocket, authentication):
    while True:
        input_string = input("> ")
        message = string_to_message(input_string, authentication["Username"])
        clientSocket.send(dumps(message).encode())
        time.sleep(0.5)
def recv_func(clientSocket, authentication):
    while True:
        ack = clientSocket.recv(1024)
        if len(ack) == 0:
           break
        sys.stdout.write(ack.decode())
        sys.stdout.write("\n> ")
        time.sleep(0.5)
    
# requesting connection
'''
- When a new client program is started, it creates a TCP connection with the known server
- Server-side will ask for login details over this connection
    - if correct, TCP connection will be maintained
    - else, TCP connection closed
'''
try:
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
except:
    print("Unable to connect to Server at this time. Please try again later.")
    exit()

# if connected, go here
while True:
    username = input("Please enter your username: ")
    password = input("Please enter your password: ")
    authentication = {
        "Username":username,
        "Password":password
    }
    clientSocket.send(dumps(authentication).encode())
    ack = clientSocket.recv(1024).decode()
    print(ack)
    if ack == "proceed":
        send_thread = threading.Thread(target=send_func, daemon=True, args=(clientSocket,authentication))
        recv_thread = threading.Thread(target=recv_func, daemon=False, args=(clientSocket,authentication))
        send_thread.start()
        recv_thread.start()
        break
    elif ack != "again":
        break
