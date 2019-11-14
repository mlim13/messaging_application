import sys
import threading
from socket import *
from json import dumps, loads
from database import *
from datetime import datetime
import time
from database import database
import copy

def is_authenticated(authentication): # authentication is a user, password dict
    '''
    - a localised check of a single 'authentication' dict to see if it's is valid
    '''
    username = authentication["Username"]
    password = authentication["Password"]
    with open('Credentials.txt', 'r') as my_file:
        lines = my_file.readlines()
        for line in lines:
            if username == line.split()[0] and password == line.split()[1]:
                return True
    return False

def is_blocked(username):
    return username in database.username_blocked and datetime.now() < database.username_blocked[username]

def authentication_process(connectionSocket):
    '''
    - takes in a username and proceeds to handle all the authentication, retries etc associated with it
    '''
    authentication = connectionSocket.recv(1024)
    authentication = loads(authentication.decode())
    username = authentication["Username"]
    while True: # we will infinite loop and conidtionally break from within the loop
        database.remove_blocks()
        if database.is_username_in_credentials(username): 
            database.increment_attempt(username)
            if is_authenticated(authentication) and not is_blocked(username):
                database.reset_attempt(authentication["Username"])                
                if database.is_online(username):
                    connectionSocket.send("already_logged_in".encode())
                    return False, authentication
                connectionSocket.send("proceed".encode())
                database.go_online(username) # adds user to list on online users and provides timestamp for login
                return True, authentication # successful authentication. Return True and the authentication dict
            if database.is_attempt_excessive(username):
                database.add_block(username)
            if is_blocked(username):
                connectionSocket.send("break".encode())
                connectionSocket.close()
                return False, authentication # too many attempts. Exit
        connectionSocket.send("again".encode())
        authentication = connectionSocket.recv(1024)
        authentication = loads(authentication.decode())
        username = authentication["Username"]  

def message_recv(connectionSocket, message):
    sender = message["Sender"]
    receiver = message["User"]
    if message["Command"] == "notification": # different behaviour if this is a notification
        if not database.is_A_blocked_by_B(receiver, sender):
            database.messages.append(message)
    else:
        if database.is_A_blocked_by_B(sender, receiver):
            if message["Command"] == "message":
                connectionSocket.send("soz bro youve been BLOCKED".encode())
            elif message["Command"] == "broadcast": # slightly different response message depending on pm or broadcast
                connectionSocket.send("oof someone's blocked you man".encode())
        elif not database.is_username_in_credentials(receiver) or sender == receiver:
            connectionSocket.send("Invalid recipient".encode())
        else:
            database.messages.append(message)

def message_send(connectionSocket, authentication):
    new_messages = []
    for msg in database.messages:
        if msg["User"] == authentication["Username"] and database.is_online(authentication["Username"]):
            connectionSocket.send((msg["Sender"] + ": " + msg["Payload"]).encode())
            time.sleep(0.2)       
        else:
            new_messages.append(msg)
        database.messages = new_messages

def broadcast(connectionSocket, message):
    for user in database.online_users:
        # python is a tricky boi about copying
        # bascially everything is copied by reference
        # since we are modifying message, we need to make a new DEEP copy everytime
        msg = copy.deepcopy(message)
        if user != msg["Sender"]:
            msg["User"] = user
            message_recv(connectionSocket, msg)

def whoelse(connectionSocket, message):
    # we want to send a lsit of online users, bar the user making the request
    # need to make a deep copy of the list
    online_users = copy.deepcopy(database.online_users)
    online_users.remove(message["Sender"])
    return online_users

def whoelsesince(connectionSocket, message):
    users = whoelse(connectionSocket, message)
    try:
        time = int(message["Payload"])
    except:
        print("Invalid input")
    for user in database.user_history:
        if database.user_history[user] > datetime.now() - timedelta(seconds=time):
            users.append(user)
    return users, time

def block(connectionSocket, message):
    blocker = message["Sender"]
    blockee = message["User"]
    try:
        database.block_A_by_B(blockee, blocker)
        connectionSocket.send("Successful Block".encode())
    except:
        connectionSocket.send("Invalid Block".encode())

def unblock(connectionSocket, message):
    blocker = message["Sender"]
    blockee = message["User"]
    try:
        database.unblock_A_by_B(blockee, blocker)
        connectionSocket.send("Successful unblock".encode())
    except:
        connectionSocket.send("Invalid unlock".encode())

def startprivate(connectionSocket, message):
    try:
        return database.get_mapping(message["User"])
    except:
        print("Invalid")

def create_message_template(command, user, payload, sender):
    message = {
        "Command": command,
        "User": user,
        "Payload": payload,
        "Sender": sender
    }
    return message

def create_notification(message):
    message["Command"] = "notification"
    return message

def logout(connectionSocket, authentication):
    message = create_message_template("", "", "we out", authentication["Username"])
    message = create_notification(message)
    broadcast(connectionSocket, message)
    database.go_offline(authentication["Username"])
    connectionSocket.close()

def TCP_recv(connectionSocket, addr):
    done, authentication = authentication_process(connectionSocket)
    if done: # if authentication process has been successful
        # first send out presence broadcast
        message = create_message_template("", "", "we in the house", authentication["Username"])
        message = create_notification(message)
        broadcast(connectionSocket, message)
        send_thread = threading.Thread(target=TCP_send, daemon=True, args=(connectionSocket,addr, authentication))
        send_thread.start()   
        connectionSocket.settimeout(database.timeout)          
        while True:
            try:
                message = connectionSocket.recv(1024)
            except:
                logout(connectionSocket, authentication)
                break
            message = loads(message.decode())
            if message["Command"] == "message":
                message_recv(connectionSocket, message)
            elif message["Command"] == "broadcast":
                broadcast(connectionSocket, message)
            elif message["Command"] == "whoelse":
                online_users = whoelse(connectionSocket, message)
                connectionSocket.send(("The online users are: " + dumps(online_users)).encode())      
            elif message["Command"] == "whoelsesince":
                users, since = whoelsesince(connectionSocket, message)
                connectionSocket.send((f"User online since {since} seconds ago are: " + dumps(users)).encode())                  
            elif message["Command"] == "block":
                block(connectionSocket, message)
            elif message["Command"] == "unblock":
                unblock(connectionSocket, message)                       
            elif message["Command"] == "logout":
                logout(connectionSocket, authentication)
                break
            elif message["Command"] == "startprivate":
                addr = startprivate(connectionSocket, message)
                response = create_message_template("address", "", addr, "")
                connectionSocket.send(dumps(response).encode())
            elif message["Command"] == "stopprivate":
                pass
            elif message["Command"] == "private":
                pass               
            time.sleep(0.5)       

def TCP_send(connectionSocket, addr, authentication):
    while True:
        message_send(connectionSocket, authentication) # continually send any pending messages 
        time.sleep(0.5)

database.block_time = int(sys.argv[1])
database.timeout = int(sys.argv[2])
# creating welcoming socket
serverPort = 12000 
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(1)
print ("The server is ready to receive")
while True:
    '''
    - we need to create a send and receive thread for EACH new TCP connection
    - this will allow sending and receiving to happen 'simultaneously' for each connection
    '''
    connectionSocket, addr = serverSocket.accept()
    recv_thread = threading.Thread(target=TCP_recv, daemon=True, args=(connectionSocket,addr))
    recv_thread.start()
