# this is just a python file to resemble very basic data storage and some other backend functionality
from datetime import datetime, timedelta
import random

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
    def remove_mapping(self, username):
        if username in self.addr_mapping:
            del self.addr_mapping[username]
    
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
    def go_online(self, username, addr):
        if self.is_username_in_credentials(username):
            self.online_users.append(username)
            self.add_mapping(username, addr)
            if username in self.user_history:
                del self.user_history[username]

    @classmethod
    def is_online(self, username):
        return username in self.online_users

    @classmethod
    def go_offline(self, username):
        if username in self.online_users:
            self.online_users.remove(username)
            self.update_history(username)
            self.remove_mapping(username)

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

# for p2p file transfer
class tracker:

    files = {}
    num_chunks = {}
    base_size = {}

    @classmethod
    # add file and an associated chunk and peer
    def add_file(self, filename, chunk_name, chunk_size, peer):
        if filename not in self.files:
            self.files[filename] = {}
            self.files[filename][chunk_name] = {}
            self.files[filename][chunk_name]["size"] = chunk_size          
            self.files[filename][chunk_name]["peers"] = set([peer])
        else:
            if chunk_name not in self.files[filename]:
                self.files[filename][chunk_name] = {}
                self.files[filename][chunk_name]["size"] = chunk_size          
                self.files[filename][chunk_name]["peers"] = set([peer])
            else:
                self.files[filename][chunk_name]["peers"].add(peer)

    @classmethod
    # add info about the total number of chunks for a file
    def set_num_chunks(self, filename, num_chunks):
        if filename in self.num_chunks:
            self.num_chunks[filename] = num_chunks

    @classmethod
    def get_num_chunks(self, filename):
        if filename in self.num_chunks:
            return self.num_chunks[filename]

    @classmethod
    # returns peers who have at least one chunk of a file
    def has_some_of_file(self, filename):
        if filename in self.files:
            peers = set()
            for chunk in self.files[filename]:
                peers = peers.union(self.files[filename][chunk]["peers"])
            if len(peers) == 0:
                return []
            return list(peers)

    @classmethod
    # returns peers who have a specific chunk of a file
    def has_chunk(self, filename, chunk_name):
        if filename in self.files and chunk_name in self.files[filename]:
            return list(self.files[filename][chunk_name]["peers"])
    
    @classmethod
    # for a given file, rarest chunk
    def get_rarest_chunk(self, filename):
        if filename in self.files:
            num_chunks = self.num_chunks[filename]
            rarity = 1000 # some arbitrarily large number
            rarest_chunks = []
            for chunk in self.files[filename]:
                length = len(self.files[filename][chunk]["peers"])
                if length == rarity:
                    rarest_chunks.append(chunk) # so we get a list of all equal rarests
                elif length < rarity:
                    rarest_chunks = []
                    rarest_chunks.append(chunk)
            # if there is more than one rarest, we randomise so we only return one
            num_rarest = len(rarest_chunks)
            index = random.randint(0, num_rarest - 1)
            rarest_chunk = rarest_chunks[index]
            return rarest_chunk
