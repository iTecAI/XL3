from util import *
import os, time
from _runtime import server

class BaseItem:
    def __init__(self):
        self.updated = False
    def update(self):
        self.updated = True
    def check(self):
        temp = self.updated
        self.updated = False
        return temp
class Connection(BaseItem):
    def __init__(self):
        super().__init__()
        self.user: User = User('','','','',cache=False)
        self.uid = None
        self.logged_in = False
        self.timeout = time.time()+5

class User(BaseItem):
    def __init__(self,uid,usn,pswhash,display_name,cache=True,connection=None):
        super().__init__()
        self.uid: str = uid
        self.username: str = usn
        self.password_hash: str = pswhash
        self.settings = {
            'display_name':display_name
        }
        if cache:
            self.cachePath = os.path.join('database','users',self.uid+'.pkl')
        self.connection = connection
    def update(self):
        super().update()
        store_user(self.uid)

def update_user_registry(uid):
    if type(server.users[uid]) != str:
        with open(os.path.join('database','users','registry.json'),'r') as f:
            reg = json.load(f)
        reg[uid] = {'username':server.users[uid].username,'connection':server.users[uid].connection}
        with open(os.path.join('database','users','registry.json'),'w') as f:
            json.dump(reg,f)
def get_user_registry():
    with open(os.path.join('database','users','registry.json'),'r') as f:
        reg = json.load(f)
    return reg

def cache_user(uid):
    if type(server.users[uid]) != str and hasattr(server.users[uid],'cachePath'):
        with open(server.users[uid].cachePath,'wb') as cache:
            pickle.dump(server.users[uid],cache)
        update_user_registry(uid)
        server.users[uid] = server.users[uid].cachePath
def store_user(uid):
    if type(server.users[uid]) != str and hasattr(server.users[uid],'cachePath'):
        with open(server.users[uid].cachePath,'wb') as cache:
            pickle.dump(server.users[uid],cache)
        update_user_registry(uid)
def load_user(uid):
    if type(server.users[uid]) == str:
        with open(server.users[uid],'rb') as cache:
            server.users[uid] = pickle.load(cache)
        update_user_registry(uid)

