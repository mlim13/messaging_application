from socket import *
from json import dumps, loads
import sys
import threading
import time
import copy
import os
import io

NUM_CHUNKS = 10
# defining the (known) server parameters
serverName = sys.argv[1]
serverPort = int(sys.argv[2])

# stores our p2p sockets, indexed by usernames
p2p_sockets = {}
curr_filename = ""

def create_message_template(command, user, payload, sender):
    message = {
        "Command":command,
        "User":user,
        "Payload":payload,
        "Sender":sender
    }
    return message

def create_ack(payload):
    message = create_message_template("ack", "", payload, "")
    return message

def string_to_message(input_string, sender):
    '''
    From an inputted string ('message'), we want to return a dictionary indexed by all the required fields:
        - command
        - User
            this will be used by the Server to determine the dest IP and dest port
        - payload (either time or the message to be sent)
    '''
    global curr_filename
    # initialising message fields to be empty
    command = ""
    user = ""
    payload = ""

    try:

        input_list = input_string.split(" ", 1)
        command = input_list[0]
        if command == "message" or command == "private":
            user = input_list[1].split(" ", 1)[0]
            payload = input_list[1].split(" ", 1)[1]
        elif command == "broadcast" or command == "whoelsesince":
            payload = input_list[1]
        elif command == "block" or command == "unblock" or command == "startprivate" or command == "stopprivate":
            user = input_list[1]
        # here are our p2p filetransfer commands
        elif command == "register":
            # different from the spec, our "register" command will not have args
            filename = input_list[1]
            num_chunks = NUM_CHUNKS
            payload = [filename, num_chunks]
        elif command == "searchFile":
            filename = input_list[1].split(" ", 1)[0]
            payload = filename
        elif command == "searchChunk":
            filename = input_list[1].split(" ")[0]
            # all remaining args are the chunks we are registering
            chunks = input_list[1].split(" ")[1:]
            chunks = list(dict.fromkeys(chunks)) # deleting duplicates
            payload = (filename, chunks)
        elif command == "download":
            filename = input_list[1].split(" ", 1)[0]
            payload = filename
        elif command == "single":
            user = input_list[1].split(" ", 1)[0]
            filename = input_list[1].split(" ", 2)[1]
            curr_filename = filename
            payload = filename
        elif command == "logout" or command == "whoelse":
            pass
        else:
            sys.stdout.write("Invalid request")
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()

            return None

        message = {
            "Command": command,
            "User": user,
            "Payload": payload,
            "Sender": sender
        }
        return message

    except:
        sys.stdout.write("Invalid request")
        sys.stdout.write("\n")
        sys.stdout.write("> ")
        sys.stdout.flush()
        return None

def send_func(clientSocket, authentication):
    # function handles our sending of data to the server
    global p2p_sockets
    while True:
        input_string = input("")
        message = string_to_message(input_string, authentication["Username"])
        if message is None:
            continue
        if message["Command"] == "private":
            recipient = message["User"]
            if recipient in p2p_sockets:
                try:
                    p2p_sockets[recipient].send(dumps(message).encode())
                except:
                    print("User is not available at this address anymore.")
                    p2p_sockets[recipient].close()
                    del p2p_sockets[recipient]
                sys.stdout.write("> ")
            else:
                sys.stdout.write("Invalid recipient")
                sys.stdout.write("\n")
                sys.stdout.write("> ")
                sys.stdout.flush()
        elif message["Command"] == "stopprivate":
            recipient = message["User"]
            if recipient in p2p_sockets:
                reverse_response = create_message_template("del", message["Sender"], "", "")
                p2p_sockets[recipient].send(dumps(reverse_response).encode())
                p2p_sockets[recipient].shutdown(SHUT_RDWR)
                p2p_sockets[recipient].close()
                del p2p_sockets[recipient]
                sys.stdout.write("> ")
                sys.stdout.flush()
            else:
                sys.stdout.write("No P2P connection exists here.")
                sys.stdout.write("\n")
                sys.stdout.write("> ")
                sys.stdout.flush()
        elif message["Command"] == "register":
            filename = message["Payload"][0]
            if os.path.exists(filename):
                total_bytes = os.path.getsize(filename)
                message["Payload"].append(total_bytes)
                clientSocket.send(dumps(message).encode())
                sys.stdout.write("> ")
                sys.stdout.flush()            
            else:
                sys.stdout.write("File does not exist.")
                sys.stdout.write("\n")
                sys.stdout.write("> ")
                sys.stdout.flush()
        elif message["Command"] == "download":
            clientSocket.send(dumps(message).encode())
            sys.stdout.write("> ")
            sys.stdout.flush()
        elif message["Command"] == "single":
            recipient = message["User"]
            if recipient in p2p_sockets:
                p2p_sockets[recipient].send(dumps(message).encode())
                sys.stdout.write("> ")
            else:
                sys.stdout.write("Invalid recipient")
                sys.stdout.write("\n")
                sys.stdout.write("> ")
                sys.stdout.flush()
        elif message["Command"] == "logout":
            for recipient in p2p_sockets:
                reverse_response = create_message_template("del", message["Sender"], "", "")
                p2p_sockets[recipient].send(dumps(reverse_response).encode())
                p2p_sockets[recipient].shutdown(SHUT_RDWR)
                p2p_sockets[recipient].close()
            del p2p_sockets
            clientSocket.send(dumps(message).encode())
            sys.stdout.write("> ")
            sys.stdout.flush()
        else:
            clientSocket.send(dumps(message).encode())
            sys.stdout.write("> ")
            sys.stdout.flush()
        time.sleep(0.5)

def recv_func(clientSocket, authentication):
    # this function deals with our received data from the server
    global p2p_sockets
    while True:
        response = clientSocket.recv(1024)
        if len(response) == 0:
           break
        response = loads(response.decode())
        # depending on the response, client performs different actions
        if response["Command"] == "ack":
            sys.stdout.write(response["Payload"])
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()
        elif response["Command"] == "message" or response["Command"] == "broadcast":
            sys.stdout.write(response["Sender"])
            sys.stdout.write(": ")
            sys.stdout.write(response["Payload"])
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()
        elif response["Command"] == "notification":
            sys.stdout.write(response["Sender"])
            sys.stdout.write("-> ")
            sys.stdout.write(response["Payload"])
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()
        elif response["Command"] == "whoelse":
            sys.stdout.write("The other online users are: ")
            sys.stdout.write(str(response["Payload"]))
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()
        elif response["Command"] == "whoelsesince":
            since = response["Payload"][1]
            sys.stdout.write(f"The users have been online since {since} seconds ago are: ")
            sys.stdout.write(str(response["Payload"][0]))
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()
        elif response["Command"] == "address":
            p2p_addr = response["Payload"]
            try:
                p2p_socket = socket(AF_INET, SOCK_STREAM)
                p2p_socket.connect(tuple(p2p_addr))
                user = response["User"]
                p2p_sockets[user] = p2p_socket
                # since TCP is bidirectional, we want to update our TCP dict in the other direction too
                reverse_response = create_message_template("address", response["Sender"], "", "")
                p2p_sockets[user].send(dumps(reverse_response).encode())
                p2p_recv_thread = threading.Thread(target=p2p_recv_func, daemon=True, args=(p2p_socket,authentication))
                p2p_recv_thread.start()
                sys.stdout.write("P2P connection initiated")
                sys.stdout.write("\n")
                sys.stdout.write("> ")
                sys.stdout.flush()
            
            except:
                sys.stdout.write("Unable to conenct to client.")
                sys.stdout.write("\n")
                sys.stdout.write("> ")
                sys.stdout.flush()
            
        elif response["Command"] == "peers":
            sys.stdout.write("The peers with the desired chunks are: ")
            sys.stdout.write(str(response["Payload"]))
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()
        elif response["Command"] == "download":
            base_size = response["Payload"]["base_size"]
            chunk_name = response["Payload"]["chunk_name"]
            sys.stdout.write("downloaded bby")
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()

        time.sleep(0.1)

def p2p_recv_func(p2p_socket, authentication):
    global p2p_sockets
    global curr_filename
    while True:
        try: # use this to also check if this socket is alive
            p2p_socket.setblocking(True)
        except:
            continue
        response = p2p_socket.recv(1024)
        if len(response) == 0:
           break
        try:
            response = loads(response.decode())
        except: # if we are receiving file/chunks we dont want to json load it
            with open(curr_filename, "wb") as fh:
                while response:
                    print("Receiving file...")
                    p2p_socket.settimeout(2) # we don't want to hang here
                    fh.write(response)
                    try:
                        response = p2p_socket.recv(1024)
                    except: # catch timeout
                        sys.stdout.write("Done.")
                        sys.stdout.write("\n")
                        sys.stdout.write("> ")
                        sys.stdout.flush()
                        break
            continue
        if response["Command"] == "ack":
            sys.stdout.write(response["Payload"])
            sys.stdout.write("\n")
            sys.stdout.write("> ")
            sys.stdout.flush()
        elif response["Command"] == "del":
            del p2p_sockets[response["User"]]
        elif response["Command"] == "address":
            user = response["User"]
            p2p_sockets[user] = p2p_socket
        elif response["Command"] == "stopprivate":
            user = response["User"]
            del p2p_sockets[user]
        elif response["Command"] == "single":
            reply_to = response["Sender"]
            filename = response["Payload"]
            if not os.path.exists(filename):
                ack = create_ack("This user does not have requested file.")
                p2p_sockets[reply_to].send(dumps(ack).encode())
            else:
                with open(filename, "rb") as my_file:
                    byte = my_file.read(1024)
                    while byte:
                        p2p_sockets[reply_to].send(byte)
                        byte = my_file.read(1024)

        else:
            sys.stdout.write(response["Sender"])
            sys.stdout.write("(private): ")
            sys.stdout.write(response["Payload"])
            sys.stdout.write("\n")
            sys.stdout.write("> ")
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
    sys.stdout.write("Unable to connect to Server at this time. Please try again later.")
    sys.stdout.write("\n")
    sys.stdout.write("> ")
    sys.stdout.flush()
    exit()

# if connected, go here
while True:
    username = input("Please enter your username: ")
    password = input("Please enter your password: ")
    authentication = {
        "Username":username,
        "Password":password,
        "Address":None
    }
    listen_socket = socket(AF_INET, SOCK_STREAM)
    listen_socket.bind(('localhost', 0))
    authentication["Address"] = listen_socket.getsockname()
    clientSocket.send(dumps(authentication).encode())
    ack = clientSocket.recv(1024)
    ack = loads(ack.decode())

    if ack["Payload"] == "proceed":
        sys.stdout.write("Welcome!")
        sys.stdout.write("\n")
        sys.stdout.write("> ")
        sys.stdout.flush()
        listen_socket.listen(1)
        send_thread = threading.Thread(target=send_func, daemon=True, args=(clientSocket,authentication))
        recv_thread = threading.Thread(target=recv_func, daemon=False, args=(clientSocket,authentication))
        listen_thread = threading.Thread(target=listen_func, daemon=True, args=(listen_socket,authentication))
        send_thread.start()
        recv_thread.start()
        listen_thread.start()
        break
    elif ack["Payload"] == "again":
        sys.stdout.write("Please try again.")
        sys.stdout.write("\n")
        sys.stdout.write("> ")
        sys.stdout.flush()
    elif ack["Payload"] == "already_logged_in":
        sys.stdout.write("Already logged in.")
        sys.stdout.write("\n")
        sys.stdout.write("> ")
        sys.stdout.flush()
        break
    else:
        sys.stdout.write("Attempts exceeded.")
        sys.stdout.write("\n")
        sys.stdout.write("> ")
        sys.stdout.flush()
        break
