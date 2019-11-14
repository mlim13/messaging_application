# this is just a python file to resemble very basic data storage and some other backend functionality
from datetime import datetime, timedelta

class database:
    # class variables, not instance variables
    block_time = 0
    timeout = 0
    messages = [] # list of messages to be sent
    online_users = [] # list of online users
    user_history = {} # dict of users and the last time they were logged in (only holds currently offline peeps)
    block_list = {} # dict indexed by username, val is a set of all respective blocked users
    addr_mapping = {} # dict maps username to an address tuple (ip address, port)

    username_attempts = {} # dict indexed by username, val is the current number of tries
    username_blocked = {} # dict indexed by username, val is the end time

    @classmethod
    def add_mapping(self, username, addr):
        self.addr_mapping[username] = addr
    
    @classmethod
    def get_mapping(self, username):
        if username in self.addr_mapping:
            return self.addr_mapping[username]
        else:
            raise Exception

    @classmethod
    def is_A_blocked_by_B(self, usernameA, usernameB):
        return usernameB in self.block_list and usernameA in self.block_list[usernameB]

    @classmethod
    def block_A_by_B(self, usernameA, usernameB):
        if self.is_username_in_credentials(usernameA) and self.is_username_in_credentials(usernameB) and usernameA != usernameB:
            if usernameB not in self.block_list:
                self.block_list[usernameB] = set()
                self.block_list[usernameB].add(usernameA)
            else:
                self.block_list[usernameB].add(usernameA)  
        else:
           raise Exception

    @classmethod
    def unblock_A_by_B(self, usernameA, usernameB):
        if self.is_username_in_credentials(usernameA) and self.is_username_in_credentials(usernameB) and usernameA != usernameB:
            if usernameB in self.block_list:
                self.block_list[usernameB].remove(usernameA)
            else:
                raise Exception 
        else:
           raise Exception

    @classmethod
    def update_history(self, username):
        if self.is_username_in_credentials(username):
            self.user_history[username] = datetime.now()

    @classmethod
    def go_online(self, username):
        if self.is_username_in_credentials(username):
            self.online_users.append(username)

    @classmethod
    def is_online(self, username):
        return username in self.online_users

    @classmethod
    def go_offline(self, username):
        if username in self.online_users:
            self.online_users.remove(username)
            self.update_history(username)

    @classmethod
    def increment_attempt(self, username):
        if self.is_username_in_credentials:
            if username not in self.username_attempts:
                self.username_attempts[username] = 1
            else:
                self.username_attempts[username] += 1
        else:
            pass 
    @classmethod
    def reset_attempt(self, username):
        self.username_attempts[username] = 0
    @classmethod
    def is_attempt_excessive(self, username):
        return self.username_attempts[username] >= 3
    @classmethod
    def is_username_in_credentials(self, username):
        with open('Credentials.txt', 'r') as my_file:
            lines = my_file.readlines()
            for line in lines:
                if username == line.split()[0]:
                    return True
        return False
    @classmethod
    def add_block(self, username):
        if username not in self.username_blocked:
            self.username_blocked[username] = datetime.now() + timedelta(seconds=self.block_time)
 
    @classmethod
    def remove_blocks(self):
        new_dict = {}
        for user in self.username_blocked:
            if self.username_blocked[user] > datetime.now():
                new_dict[user] = self.username_blocked[user]
            else:
                self.reset_attempt(user)
        self.username_blocked = new_dict


