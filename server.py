import sys
import threading
from socket import *
from json import dumps, loads
from database import *
from datetime import datetime
import time
from database import database, tracker
import copy
import math

def create_message_template(command, user, payload, sender):
    message = {
        "Command": command,
        "User": user,
        "Payload": payload,
        "Sender": sender
    }
    return message

def create_download(owner_name, owner_addr, filename, chunk_name, base_size, num_chunks):
    payload = {
        "owner_name":owner_name,
        "owner_addr":owner_addr,
        "filename":filename,
        "chunk_name":chunk_name,
        "base_size":base_size,
        "num_chunks":num_chunks,
    }
    message = {
        "Command": "download",
        "User": "",
        "Payload": payload,
        "Sender": "",
    }
    return message

def create_peers(payload):
    peers = create_message_template("peers", "", payload, "")
    return peers

def create_ack(payload):
    message = create_message_template("ack", "", payload, "")
    return message

def create_message(payload, sender):
    message = create_message_template("message", "", payload, sender)
    return message

def create_address(payload, user, sender): # user is the intended recipient
    message = create_message_template("address", user, payload, sender)
    return message

def create_whoelse(payload):
    whoelse = create_message_template("whoelse", "", payload, "")
    return whoelse

def create_whoelsesince(payload):
    whoelsesince = create_message_template("whoelsesince", "", payload, "")
    return whoelsesince

def create_notification(message):
    message["Command"] = "notification"
    return message

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
    addr = authentication["Address"]
    username = authentication["Username"]
    while True: # we will infinite loop and conidtionally break from within the loop
        database.remove_blocks()
        if database.is_username_in_credentials(username): 
            database.increment_attempt(username)
            if is_authenticated(authentication) and not is_blocked(username):
                database.reset_attempt(authentication["Username"])                
                if database.is_online(username):
                    ack = create_ack("already_logged_in")
                    connectionSocket.send(dumps(ack).encode())
                    return False, authentication
                ack = create_ack("proceed")
                connectionSocket.send(dumps(ack).encode())
                database.go_online(username, addr) # adds user to list on online users and maps address
                return True, authentication # successful authentication. Return True and the authentication dict
            if database.is_attempt_excessive(username):
                database.add_block(username)
            if is_blocked(username):
                ack = create_ack("break")
                connectionSocket.send(dumps(ack).encode())
                connectionSocket.close()
                return False, authentication # too many attempts. Exit
        ack = create_ack("again")
        connectionSocket.send(dumps(ack).encode())
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
                ack = create_ack("You have been blocked by this user")
                connectionSocket.send(dumps(ack).encode())
            elif message["Command"] == "broadcast": # slightly different response message depending on pm or broadcast
                ack = create_ack("Broadcast could not reach all users")
                connectionSocket.send(dumps(ack).encode())
        elif not database.is_username_in_credentials(receiver) or sender == receiver:
            ack = create_ack("Invalid recipient")
            connectionSocket.send(dumps(ack).encode())
        else:
            database.messages.append(message)

def message_send(connectionSocket, authentication):
    new_messages = []
    for msg in database.messages:
        if msg["User"] == authentication["Username"] and database.is_online(authentication["Username"]):
            message = create_message(msg["Payload"], msg["Sender"])
            try:
                connectionSocket.send(dumps(message).encode())
            except:
                pass
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
    since = ""
    try:
        since = int(message["Payload"])
    except ValueError:
        ack = create_ack("Invalid input")
        connectionSocket.send(dumps(ack).encode())

    for user in database.user_history:
        if database.user_history[user] > datetime.now() - timedelta(seconds=since):
            users.append(user)
    return users, since

def block(connectionSocket, message):
    blocker = message["Sender"]
    blockee = message["User"]
    try:
        database.block_A_by_B(blockee, blocker)
        ack = create_ack("Successful block")
        connectionSocket.send(dumps(ack).encode())
    except:
        ack = create_ack("Invalid block")
        connectionSocket.send(dumps(ack).encode())

def unblock(connectionSocket, message):
    blocker = message["Sender"]
    blockee = message["User"]
    try:
        database.unblock_A_by_B(blockee, blocker)
        ack = create_ack("Successful unblock")
        connectionSocket.send(dumps(ack).encode())
    except:
        ack = create_ack("Invalid unblock")
        connectionSocket.send(dumps(ack).encode())

def startprivate(connectionSocket, message):
    recipient = message["User"]
    sender = message["Sender"]
    if not database.is_username_in_credentials(recipient):
        ack = create_ack("Not a valid user")
        connectionSocket.send(dumps(ack).encode())
    elif not database.is_online(recipient):
        ack = create_ack("This user is not online")
        connectionSocket.send(dumps(ack).encode())
    elif recipient == sender:
        ack = create_ack("Private messaging cannot be started with yourself")
        connectionSocket.send(dumps(ack).encode())
    elif database.is_A_blocked_by_B(sender, recipient):
        ack = create_ack("You have been blocked by this user")
        connectionSocket.send(dumps(ack).encode())
    else:
        addr = database.get_mapping(message["User"])
        address = create_address(addr, recipient, sender)
        connectionSocket.send(dumps(address).encode())

def logout(connectionSocket, authentication):
    message = create_message_template("", "", "Logging out!", authentication["Username"])
    message = create_notification(message)
    broadcast(connectionSocket, message)
    database.go_offline(authentication["Username"])
    connectionSocket.close()

def register(connectionSocket, message):
    peer = message["Sender"]
    filename = message["Payload"][0]
    num_chunks = message["Payload"][1] # for out current client implementation, this will always be 10
    tracker.num_chunks[filename] = num_chunks
    total_bytes = message["Payload"][2]
    for num in range(num_chunks):
        chunk_size = math.floor(total_bytes/num_chunks)
        tracker.base_size[filename] = chunk_size # helps with calculating offset
        if num == num_chunks - 1: # if we're on the last chunk
            chunk_size = total_bytes%num_chunks
        tracker.add_file(filename, str(num), chunk_size, peer)
    tracker.set_num_chunks(filename, num_chunks)
    ack = create_ack("File registered.")
    connectionSocket.send(dumps(ack).encode())
    
def searchFile(connectionSocket, message):
    peer = message["Sender"]
    filename = message["Payload"]
    return tracker.has_some_of_file(filename)

def searchChunk(connectionSocket, message):
    peer = message["Sender"]
    filename = message["Payload"][0]
    chunks = message["Payload"][1]
    peers = []
    for chunk in chunks:
        new_peers = tracker.has_chunk(filename, chunk)
        if new_peers is not None:
            peers = peers + new_peers 
    peers = list(dict.fromkeys(peers)) # duplicate removal
    return peers


def download(connectionSocket, message):
    filename = message["Payload"]
    if filename in tracker.files:
        
        # first we get the num_chunks and rarest_chunk info
        num_chunks = tracker.get_num_chunks(filename)
        rarest_chunk = tracker.get_rarest_chunk(filename)
        # then we find the owner of this rarest chunk
        # if multiple owners, we pick a random one
        owners = tracker.has_chunk(filename, rarest_chunk)
        num_owners = len(owners)
        index = random.randint(0, num_owners - 1)
        owner = owners[index]
        # getting some info
        base_size = tracker.base_size[filename]
        #chunk_size = tracker.files[filename][rarest_chunk]["size"]
        num_chunks = tracker.num_chunks[filename]
        # now we find the addr of this owner
        addr = database.get_mapping(owner)
        # then we send back an "addr" message so the client knows to start a private connection
        download = create_download(owner, addr, filename, rarest_chunk, base_size, num_chunks)
        connectionSocket.send(dumps(download).encode())
    else:
        ack = create_ack("No such file.")
        connectionSocket.send(dumps(ack).encode())

def TCP_recv(connectionSocket):
    done, authentication = authentication_process(connectionSocket)
    if done: # if authentication process has been successful
        # first send out presence broadcast
        message = create_message_template("", "", "I've logged in!", authentication["Username"])
        message = create_notification(message)
        broadcast(connectionSocket, message)
        send_thread = threading.Thread(target=TCP_send, daemon=True, args=(connectionSocket, authentication))
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
                response = create_whoelse(online_users)
                connectionSocket.send(dumps(response).encode())      
            elif message["Command"] == "whoelsesince":
                users, since = whoelsesince(connectionSocket, message)
                if isinstance(since, int):
                    response = create_whoelsesince((users, since))
                    connectionSocket.send(dumps(response).encode())                 
            elif message["Command"] == "block":
                block(connectionSocket, message)
            elif message["Command"] == "unblock":
                unblock(connectionSocket, message)                       
            elif message["Command"] == "logout":
                logout(connectionSocket, authentication)
                break
            elif message["Command"] == "startprivate":
                startprivate(connectionSocket, message)
            elif message["Command"] == "stopprivate":
                # server does not handle this command - entirely p2p
                pass
            elif message["Command"] == "private":
                # server does not handle this command = entirely p2p
                pass   
            elif message["Command"] == "register":
                register(connectionSocket, message)
            elif message["Command"] == "searchFile":
                peers = searchFile(connectionSocket, message)
                peer_msg = create_peers(peers)
                connectionSocket.send(dumps(peer_msg).encode())
            elif message["Command"] == "searchChunk":
                peers = searchChunk(connectionSocket, message) 
                peer_msg = create_peers(peers)
                connectionSocket.send(dumps(peer_msg).encode())   
            elif message["Command"] == "download":
                download(connectionSocket, message)
            time.sleep(0.8)       

def TCP_send(connectionSocket, authentication):
    while True:
        message_send(connectionSocket, authentication) # continually send any pending messages 
        time.sleep(0.2)

database.block_time = int(sys.argv[2])
database.timeout = int(sys.argv[3])
# creating welcoming socket
serverPort = int(sys.argv[1]) 
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
    recv_thread = threading.Thread(target=TCP_recv, daemon=True, args=(connectionSocket,))
    recv_thread.start()
