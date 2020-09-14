import json
from api.api_utils import defaults
import random, hashlib, time
from classes import BaseItem
import pickle
from _runtime import server
import gc, os

ITEMS = [
    'name','race','class_display','classes','level','xp','proficiency_bonus','speed',
    'alignment','passive_perception','ac','max_hp','hp','thp','init','init_adv','init_mod','inspiration','equipped_items','death_saves','hit_dice','attacks','abilities','skills',
    'other_profs','spellcasting','resist','vuln','immune','image','background','traits','languages','physical','backstory',
    'features','inventory','options','owner','id','campaign'
]

class Character(BaseItem):
    def __init__(self,options={},**kwargs):
        super().__init__()
        self.options = defaults(options,{
            'public':True,
            'variant_encumbrance':False,
            'coin_weight':True,
            'roll_hp':False
        })
        self.owner = ''
        self.campaign = ''
        self.id = hashlib.sha256(str(int(time.time())+random.random()).encode('utf-8')).hexdigest()

    def to_dict(self):
        return {i:getattr(self,i,None) for i in ITEMS}
    def to_json(self,indent=None):
        return json.dumps(self.to_dict(),indent=indent,separators=(',', ':'))

    @classmethod
    def from_dict(cls,dct):
        instance = cls(options=dct['options'])
        for i in ITEMS:
            setattr(instance,i,dct[i])
        return instance
    
    @classmethod
    def from_json(cls,_json):
        return Character.from_dict(json.loads(_json))

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
    def inventory_calculate(self):
        self.inventory['total_coin'] = round(sum([i['amount']*i['conversion'] for i in self.inventory['coin']]),2)
        self.inventory['total_wealth'] = round(sum([sum([k['quantity']*k['cost'] for k in i['items']]) for i in self.inventory['containers']]),2)
        self.inventory['current_weight'] = round(sum([sum([k['quantity']*k['weight'] for k in i['items']]) for i in self.inventory['containers']]),2)
        for i in self.inventory['containers']:
            i['current_weight'] = round(sum([k['quantity']*k['weight'] for k in i['items']]),2)
            if i['coin_container'] and self.options['coin_weight']:
                i['current_weight'] += round(sum([k['amount']*k['weight'] for k in self.inventory['coin']]),2)
                i['current_weight'] = round(i['current_weight'],2)
        if self.options['coin_weight']:
            self.inventory['current_weight'] += round(sum([k['amount']*k['weight'] for k in self.inventory['coin']]),2)
            self.inventory['current_weight'] = round(self.inventory['current_weight'],2)
