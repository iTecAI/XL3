import json, d20
from api.api_utils import defaults, cond
from api.open5e import get5e
import random, hashlib, time
from classes import *
import pickle
from _runtime import server
import gc, os

ITEMS = [
    'name','race','class_display','classes','level','xp','proficiency_bonus','speed',
    'alignment','passive_perception','ac','max_hp','hp','thp','init','init_adv','init_mod','inspiration','equipped_items','death_saves','hit_dice','attacks','abilities','skills',
    'other_profs','weapon_profs','armor_profs','spellcasting','currently_displayed','resist','vuln','immune','image','background','traits','languages','physical','backstory',
    'features','inventory','options','owner','id','campaign','spell_slots'
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
        self.version = 0

    def to_dict(self):
        return {i:getattr(self,i,None) for i in ITEMS}
    def to_json(self,indent=None):
        return json.dumps(self.to_dict(),indent=indent,separators=(',', ':'))
    def update(self):
        load_user(self.owner)
        try:
            server.connections[server.users[self.owner].connection].endpoints['characters'] = True
        except KeyError:
            pass
        if (len(self.campaign) > 0):
            for c in server.connections.keys():
                if self.campaign in server.connections[c].user.owned_campaigns or self.campaign in server.connections[c].user.participating_campaigns:
                    server.connections[c].endpoints['characters'] = True
                    server.connections[c].endpoints['campaigns'] = True

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
        ct = 0
        eq_index = -1
        for c in self.inventory['containers']: # Delete item listings with a qt of 0
            if c['name'] == 'equipped':
                eq_index = ct
            new_items = []
            for i in range(len(c['items'])):
                if c['items'][i]['quantity'] > 0:
                    new_items.append(c['items'][i])
            self.inventory['containers'][ct]['items'] = new_items
            ct += 1

        self.inventory['total_coin'] = round(sum([i['amount']*i['conversion'] for i in self.inventory['coin']]),2) # calculates coin total
        self.inventory['total_wealth'] = round(sum([sum([k['quantity']*k['cost'] for k in i['items']]) for i in self.inventory['containers']]),2) # calculates item wealth
        self.inventory['current_weight'] = round(sum([sum([k['quantity']*k['weight'] for k in i['items']]) for i in self.inventory['containers'] if i['apply_weight']]),2) # gets current weight, respecting apply_weight values
        for i in self.inventory['containers']: # calculates inv weight
            i['current_weight'] = round(sum([k['quantity']*k['weight'] for k in i['items']]),2)
            if i['coin_container'] and self.options['coin_weight']:
                i['current_weight'] += round(sum([k['amount']*k['weight'] for k in self.inventory['coin']]),2)
                i['current_weight'] = round(i['current_weight'],2)
        if self.options['coin_weight'] and any([c['coin_container'] and c['apply_weight'] for c in self.inventory['containers']]): # calculates coin weight if necessary
            self.inventory['current_weight'] += round(sum([k['amount']*k['weight'] for k in self.inventory['coin']]),2)
            self.inventory['current_weight'] = round(self.inventory['current_weight'],2)
        
        if eq_index >= 0:
            _weapons = {i['slug']:i for i in get5e('weapons')}
            _armor = {i['slug']:i for i in get5e('armor')}
            shield_mod = 0
            self.ac['base'] = 10
            for item in self.inventory['containers'][eq_index]['items']:
                if item['type'] == 'armor' and item['slug'] in _armor.keys():
                    if _armor[item['slug']]['type'] == 'light':
                        self.ac['base'] = _armor[item['slug']]['ac'] + self.abilities['dexterity']['mod']
                    elif _armor[item['slug']]['type'] == 'medium':
                        self.ac['base'] = _armor[item['slug']]['ac'] + min([self.abilities['dexterity']['mod'],2])
                    elif _armor[item['slug']]['type'] == 'heavy':
                        self.ac['base'] = _armor[item['slug']]['ac']
                    elif _armor[item['slug']]['type'] == 'shield':
                        shield_mod += _armor[item['slug']]['ac']
            self.ac['base'] += shield_mod
    
    def recieve_attack(self,atk,adv=None,bonus_override=None):
        if not atk['automated']:
            raise ValueError('Attack is not automated.')

        data_register = {
            'hit':False,
            'damage':0,
            'damage_str':'',
            'damage_raw':'',
            'roll_total':0,
            'roll_str':''
        }
        if bonus_override != None:
            bonus = bonus_override
        else:
            if 'bonus' in atk.keys():
                bonus = atk['bonus']
            else:
                bonus = atk['bonus_mod']
        if adv == 'adv':
            adstr = 'kh1'
            ad2 = '2'
        elif adv == 'dis':
            adstr = 'kl1'
            ad2 = '2'
        else:
            adstr = ''
            ad2 = ''
        roll = d20.roll(ad2+'d20'+adstr+cond(bonus<0,'','+')+str(bonus))
        data_register['roll_total'] = roll.total
        data_register['roll_str'] = str(roll)
        if roll.total >= self.ac['base'] + self.ac['mod']:
            data_register['hit'] = True
            dmg_str = ''
            for d in atk['damage']:
                dmg_str += '('
                if len(d['mods']) == 0:
                    mods = ['nonmagical']
                else:
                    mods = d['mods'][:]
                dmg_str += d['roll']
                if d['type'].lower() in self.vuln.keys():
                    if any([i in self.vuln[d['type'].lower()]['damage_condtion'] for i in mods]) or len(self.vuln[d['type'].lower()]['damage_condtion']) == 0:
                        dmg_str += '*2'
                if d['type'].lower() in self.resist.keys():
                    if any([i in self.resist[d['type'].lower()]['damage_condtion'] for i in mods]) or len(self.resist[d['type'].lower()]['damage_condtion']) == 0:
                        dmg_str += '/2'
                if d['type'].lower() in self.immune.keys():
                    if any([i in self.immune[d['type'].lower()]['damage_condtion'] for i in mods]) or len(self.immune[d['type'].lower()]['damage_condtion']) == 0:
                        dmg_str += '*0'
                dmg_str += ')+'
            dmg_str = dmg_str.strip('+')
            data_register['damage_raw'] = dmg_str
            dmg_roll = d20.roll(dmg_str)
            data_register['damage'] = dmg_roll.total
            data_register['damage_str'] = str(dmg_roll)
            self.hp -= dmg_roll.total
            if self.hp > self.max_hp:
                self.hp = self.max_hp+0
            if self.hp < 0:
                self.hp = 0
            self.update()
            self.cache()
        
        return data_register
        
    
