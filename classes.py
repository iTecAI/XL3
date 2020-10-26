from util import *
import os, time, random
from _runtime import server, CONFIG
import secrets
import pickle

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
        self.char_update = BaseItem()
        self.camp_update = BaseItem()

class Campaign(BaseItem):
    def __init__(self,owner,name):
        super().__init__()
        self.id = secrets.token_urlsafe(16) # Generate 16-byte unique ID for campaign
        self.owner = owner
        self.name = name
        self.characters = []
        self.settings = {
            'variant_encumbrance':{
                'display_name':'Variant Encumbrance',
                'type':bool,
                'value':False
            },
            'coin_weight':{
                'display_name':'Coin Weight',
                'type':bool,
                'value':True
            },
            'roll_hp':{
                'display_name':'Roll HP',
                'type':bool,
                'value':False
            },
            'max_characters':{
                'display_name':'Character Limit',
                'type':int,
                'min':0,
                'max':30,
                'value':5
            }
        }
        self.maps = {}

        self.update()
    def update(self):
        with open(os.path.join('database','campaigns','registry.json'),'r') as f:
            registry = json.load(f)
        registry[self.id] = {'id':self.id,'owner':self.owner,'name':self.name}
        with open(os.path.join('database','campaigns','registry.json'),'w') as f:
            json.dump(registry,f)
        with open(os.path.join('database','campaigns',self.id+'.pkl'),'w') as f:
            pickle.dump(self,f)
    def to_json(self):
        return {
            'id':self.id,
            'owner':self.owner,
            'name':self.name,
            'characters':self.characters,
            'settings':self.settings,
            'maps':self.maps
        }
    
    @classmethod
    def load(cls,cid):
        if os.path.exists(os.path.join('database','campaigns',cid+'.pkl')):
            with open(os.path.join('database','campaigns',cid+'.pkl'),'r') as f:
                item = pickle.load(f)
                item.update()
                return item
        else:
            raise KeyError('Character '+str(cid)+' does not exist.')

class User(BaseItem):
    def __init__(self,uid,usn,pswhash,display_name,cache=True,connection=None):
        super().__init__()
        self.uid: str = uid
        self.username: str = usn
        self.password_hash: str = pswhash
        self.settings: dict = {
            'display_name':display_name
        }
        if cache:
            self.cachePath: str = os.path.join('database','users',self.uid+'.pkl')
        self.connection: Connection = connection
        self.owned_characters: list = []
        self.owned_campaigns: list = []
        self.participating_campaigns: list = []
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

