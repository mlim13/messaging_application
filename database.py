# this is just a python file to resemble a very basic database
from datetime import datetime, timedelta

class database:
    # class variables, not instance variables
    block_time = 0
    messages = [] # list of messages to be sent
    online_users = [] # lsit of the usernames of online users

    username_attempts = {} # dict indexed by username, val is the current number of tries
    username_blocked = {} # dict indexed by username, val end time
    @classmethod
    def initialise_attempts(self):
        my_file = open('Credentials.txt', 'r')
        users = my_file.readlines()
        for user in users:
            self.username_attempts[user.split()[0]] = 0
        my_file.close()
    @classmethod
    def increment_attempt(self, username):
        self.username_attempts[username] += 1    
    @classmethod
    def reset_attempt(self, username):
        self.username_attempts[username] = 0
    @classmethod
    def is_attempt_excessive(self, username):
        return self.username_attempts[username] >= 3
    @classmethod
    def is_username_in_credentials(self, username):
        return username in self.username_attempts
    @classmethod
    def add_block(self, username):
        print("add block called")
        if username not in self.username_blocked:
            self.username_blocked[username] = datetime.now() + timedelta(seconds=self.block_time)
 
    @classmethod
    def remove_blocks(self):
        print("remove blocks called")
        new_dict = {}
        for user in self.username_blocked:
            if self.username_blocked[user] > datetime.now():
                new_dict[user] = self.username_blocked[user]
            else:
                self.reset_attempt(user)
        self.username_blocked = new_dict


