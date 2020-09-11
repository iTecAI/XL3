import json
from api.api_utils import defaults
import random, hashlib, time
from classes import BaseItem
import pickle
from _runtime import server
import gc, os

class Character(BaseItem):
    def __init__(self,options={},**kwargs):
        super().__init__()
        self.options = defaults(options,{
            'public':True
        })
        self.owner = ''
        self.campaign = ''
        self.id = hashlib.sha256(str(int(time.time())+random.random()).encode('utf-8')).hexdigest()
    def to_dict(self):
        items = [
            'name','race','class_display','classes','level','xp','prof','speed',
            'alignment','ac','max_hp','hp','init','attacks','abilities','skills',
            'other_profs','spellcasting','resist','vuln','immune','image'
            ]
        return {i:getattr(self,i,None) for i in items}

    def to_json(self,indent=None):
        return json.dumps(self.to_dict(),indent=indent)
    def cache(self,delete=False):
        with open(os.path.join('database','characters','registry.json'),'r') as f:
            reg = json.load(f)
        reg[self.id] = {
            'id':self.id,
            'owner':self.owner,
            'campaign':self.campaign,
            'public':self.options['public']
        }
        with open(os.path.join('database','characters','registry.json'),'w') as f:
            json.dump(reg,f)
        with open(os.path.join('database','characters',self.id+'.pkl'),'wb') as f:
            pickle.dump(self,f)
        if self.id in server.characters.keys() and delete:
            del server.characters[self.id]
            gc.collect()