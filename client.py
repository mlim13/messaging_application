from socket import *
from json import dumps, loads
import sys
import threading
import time
import copy

# defining the (known) server parameters
serverName = 'localhost'
serverPort = 12000

outgoing_messages = []

def create_message_template(command, user, payload, sender):
    message = {
        "Command": command,
        "User": user,
        "Payload": payload,
        "Sender": sender
    }
    return message

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

    input_list = input_string.split(" ", 1)
    command = input_list[0]
    if command == "message" or command == "private":
        user = input_list[1].split(" ", 1)[0]
        payload = input_list[1].split(" ", 1)[1]
    elif command == "broadcast" or command == "whoelsesince":
        payload = input_list[1]
    elif command == "block" or command == "unblock" or command == "startprivate" or command == "stopprivate":
        user = input_list[1]

    message = {
        "Command": command,
        "User": user,
        "Payload": payload,
        "Sender": sender
    }

    return message
 
p2p_sockets = {}

def send_func(clientSocket, authentication):
    global p2p_sockets
    while True:
        input_string = input("> ")
        message = string_to_message(input_string, authentication["Username"])
        if message["Command"] == "private":
            user = message["User"]
            p2p_sockets[user].send(dumps(message).encode())
        else:
            clientSocket.send(dumps(message).encode())
        time.sleep(0.5)

def recv_func(clientSocket, authentication):
    global p2p_sockets
    while True:
        response = clientSocket.recv(1024)
        if len(response) == 0:
           break
        response = loads(response.decode())

        # depending on the response, client performs different actions
        if response["Command"] == "ack":
            sys.stdout.write(response["Payload"])
        elif response["Command"] == "message":
            sys.stdout.write(response["Sender"])
            sys.stdout.write(": ")
            sys.stdout.write(response["Payload"])
        elif response["Command"] == "whoelse":
            sys.stdout.write("The other online users are: ")
            sys.stdout.write(str(response["Payload"]))
        elif response["Command"] == "whoelsesince":
            since = response["Payload"][1]
            sys.stdout.write(f"The users have been online since {since} seconds ago are: ")
            sys.stdout.write(str(response["Payload"][0]))
        elif response["Command"] == "address":
            p2p_addr = response["Payload"]
            print(p2p_addr)
            try:
                p2p_socket = socket(AF_INET, SOCK_STREAM)
                p2p_socket.connect(tuple(p2p_addr))
                user = response["User"]
                p2p_sockets[user] = p2p_socket
                # since TCP is bidirectional, we want to update our TCP dict in the other direction too
                reverse_response = create_message_template("address", response["Sender"], "", "")
                p2p_sockets[user].send(dumps(reverse_response).encode())
                print(reverse_response)
                p2p_recv_thread = threading.Thread(target=p2p_recv_func, daemon=True, args=(p2p_socket,authentication))
                p2p_recv_thread.start()
            except:
                print("Unable to connect to client.")

        sys.stdout.write("\n> ")
        time.sleep(0.5)

def p2p_recv_func(p2p_socket, authentication):
    global p2p_sockets
    while True:
        response = p2p_socket.recv(1024)
        if len(response) == 0:
           break
        response = loads(response.decode())
        if response["Command"] == "address":
            user = response["User"]
            p2p_sockets[user] = p2p_socket
        sys.stdout.write(response["Sender"])
        sys.stdout.write(": ")
        sys.stdout.write(response["Payload"])
        sys.stdout.write("\n")
        sys.stdout.flush()

def listen_func(listen_socket, authentication):
    while True:
        p2p_socket, p2p_addr = listen_socket.accept()
        p2p_recv_thread = threading.Thread(target=p2p_recv_func, daemon=True, args=(p2p_socket,authentication))
        p2p_recv_thread.start()

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
        "Password":password,
        "Address":clientSocket.getsockname()
    }
    clientSocket.send(dumps(authentication).encode())
    ack = clientSocket.recv(1024)
    ack = loads(ack.decode())

    if ack["Payload"] == "proceed":
        print("Welcome!")
        listen_socket = socket(AF_INET, SOCK_STREAM)
        listen_socket.bind(authentication["Address"])
        listen_socket.listen(1)
        send_thread = threading.Thread(target=send_func, daemon=True, args=(clientSocket,authentication))
        recv_thread = threading.Thread(target=recv_func, daemon=False, args=(clientSocket,authentication))
        listen_thread = threading.Thread(target=listen_func, daemon=True, args=(listen_socket,authentication))
        send_thread.start()
        recv_thread.start()
        listen_thread.start()
        break
    elif ack["Payload"] == "again":
        print("Please try again")
    elif ack["Payload"] == "already_logged_in":
        print("Already logged in")
        break
    else:
        print("Attempts exceeded")
        break
