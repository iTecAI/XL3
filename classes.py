from util import *
import os, time, random
from _runtime import server, CONFIG
import secrets
import pickle
import hashlib

class BaseItem:
    def __init__(self):
        pass
class Connection(BaseItem):
    def __init__(self):
        super().__init__()
        self.user: User = User('','','','',cache=False)
        self.uid = None
        self.logged_in = False
        self.timeout = time.time()+5
        self.endpoints = {
            'client':False,
            'connection':False,
            'characters':False,
            'campaigns':False
        }
    def check(self,endpoint):
        t = self.endpoints[endpoint] == True
        self.endpoints[endpoint] = False
        return t
    def update(self):
        self.endpoints['connection'] = True

class Campaign(BaseItem):
    def __init__(self,owner,name,password):
        super().__init__()
        self.id = secrets.token_urlsafe(16) # Generate 16-byte unique ID for campaign
        self.owner = owner
        if len(password) == 0:
            self.password_protected = False
            self.passhash = ''
        else:
            self.password_protected = True
            self.passhash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        self.name = name
        self.characters = []
        self.settings = {
            'variant_encumbrance':{
                'display_name':'Variant Encumbrance',
                'type':'bool',
                'value':False
            },
            'coin_weight':{
                'display_name':'Coin Weight',
                'type':'bool',
                'value':True
            },
            'roll_hp':{
                'display_name':'Roll HP',
                'type':'bool',
                'value':False
            },
            'max_characters':{
                'display_name':'Character Limit',
                'type':'int',
                'min':0,
                'max':int(CONFIG['CAMPAIGNS']['characters_per_campaign']),
                'value':5
            }
        }
        self.maps = {}
        self.homebrew = {}

        self.update()
    def update(self):
        with open(os.path.join('database','campaigns','registry.json'),'r') as f:
            registry = json.load(f)
        registry[self.id] = {'id':self.id,'owner':self.owner,'name':self.name}
        with open(os.path.join('database','campaigns','registry.json'),'w') as f:
            json.dump(registry,f)
        with open(os.path.join('database','campaigns',self.id+'.pkl'),'wb') as f:
            pickle.dump(self,f)
        for c in server.connections.keys():
            if self.id in server.connections[c].user.owned_campaigns or self.id in server.connections[c].user.participating_campaigns:
                server.connections[c].endpoints['campaigns'] = True
    def to_json(self):
        return {
            'id':self.id,
            'owner':self.owner,
            'name':self.name,
            'characters':self.characters,
            'settings':self.settings,
            'maps':self.maps,
            'homebrew':self.homebrew
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
        if self.connection in server.connections.keys():
            server.connections[self.connection].endpoints['client'] = True
        else:
            self.connection = None
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

