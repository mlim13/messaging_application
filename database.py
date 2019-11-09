# this is just a python file to resemble a very basic database
def add_message(messages, message, recv_user):
    if recv_user not in messages:
        messages[recv_user] = [message]
    else:
        messages[recv_user].append(message)

class message:
    def __init__(self, send_address, payload):
        self.send_address = send_address
        self.payload = payload
