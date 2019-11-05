import sys
import threading
from socket import *

# creating welcoming socket
serverPort = 12000 
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(1)

print ("The server is ready to receive")

# threads take in a function as input
# the threads stay alive until the function ends
# therefore, we need to create functions containing an infinite loop that does all the requried TCP functionality
def TCP_connection(connectionSocket, addr):
    while True:
        sentence = connectionSocket.recv(1024)
        sentence = sentence.upper()
        connectionSocket.send(sentence)

while True:
    connectionSocket, addr = serverSocket.accept()
    thread = threading.Thread(target=TCP_connection, daemon=True, args=(connectionSocket,addr))
    thread.start()

        
   