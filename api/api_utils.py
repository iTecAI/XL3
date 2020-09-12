import d20, re, json

import pickle
import os.path
from googleapiclient.discovery import build
from google.oauth2 import service_account

SKILLS = {
    'acrobatics':'dexterity',
    'animal_handling':'wisdom',
    'arcana':'intelligence',
    'athletics':'strength',
    'deception':'charisma',
    'history':'intelligence',
    'insight':'wisdom',
    'intimidation':'charisma',
    'investigation':'intelligence',
    'medicine':'wisdom',
    'nature':'intelligence',
    'perception':'wisdom',
    'performance':'charisma',
    'persuasion':'charisma',
    'religion':'intelligence',
    'sleight_of_hand':'dexterity',
    'stealth':'dexterity',
    'survival':'wisdom'
}

DAMAGETYPES = ['acid', 'bludgeoning', 'cold', 'fire', 'force', 'lightning', 'necrotic', 'piercing', 'poison', 'psychic', 'radiant', 'slashing', 'thunder']

CONDITIONS = ['blinded','charmed','deafened','fatigued','frightened','grappled','incapacitated','invisible','paralyzed','petrified','poisoned','prone','restrained','stunned','unconscious','exhaustion']

CASTERS = ['bard','cleric','druid','paladin','ranger','sorcerer','warlock','wizard']

ABILITIES = ['strength','dexterity','constitution','intelligence','wisdom','charisma']

def split_on(string,seps):
    ret = string.split(seps.pop())
    for sep in seps:
        nret = []
        for item in ret:
            nret.extend(item.split(sep))
        ret = nret[:]
    return ret

def base10(string):
    dat = ''.join(re.findall(r'[0-9]',string))
    if dat == '':
        dat = '0'
    return dat

def alpha(string):
    return ''.join(re.findall(r'[a-zA-Z ]',string))

def defaults(inp, default):
    for k in default.keys():
        if not k in inp.keys():
            inp[k] = default[k]
    return inp

def getmod(score):
    score = int(score)
    if score > 0 and score < 31:
        return [
            -5,
            -4,
            -4,
            -3,
            -3,
            -2,
            -2,
            -1,
            -1,
            0,
            0,
            1,
            1,
            2,
            2,
            3,
            3,
            4,
            4,
            5,
            5,
            6,
            6,
            7,
            7,
            8,
            8,
            9,
            9,
            10
        ][score-1]
    else:
        return 0

class Creature:
    def __init__(self,options={},**kwargs):
        self.data = self.get_creature_info(kwargs)
        self.options = defaults(options,{
            'rollhp':False
        })
        self.setup()
        
    def get_creature_info(self,kwargs):
        return {
            "slug": "",
            "name": "",
            "size": "",
            "type": "",
            "subtype": "",
            "group": None,
            "alignment": "",
            "armor_class": 0,
            "armor_desc": "",
            "hit_points": 0,
            "hit_dice": "0",
            "speed": {
                "walk": 0
            },
            "strength": 0,
            "dexterity": 0,
            "constitution": 0,
            "intelligence": 0,
            "wisdom": 0,
            "charisma": 0,
            "strength_save": None,
            "dexterity_save": None,
            "constitution_save": None,
            "intelligence_save": None,
            "wisdom_save": None,
            "charisma_save": None,
            "perception": None,
            "skills": {},
            "damage_vulnerabilities": "",
            "damage_resistances": "",
            "damage_immunities": "",
            "condition_immunities": "",
            "senses": "",
            "languages": "",
            "challenge_rating": "",
            "actions": [],
            "reactions": "",
            "legendary_desc": "",
            "legendary_actions": [],
            "special_abilities": [],
            "spell_list": [],
            "img_main": None,
            "document__slug": "",
            "document__title": "",
            "document__license_url": "http://open5e.com/legal"
        }

    def _get_proficiency(self):
        profs = {
            4:2,
            8:3,
            12:4,
            16:5,
            20:6,
            24:7,
            28:8,
            30:9
        }

        for p in profs.keys():
            if self.challenge <= p:
                return profs[p]
    
    def _parse_dmg_string(self, string):
        global DAMAGETYPES
        portions = string.split('; ')
        ret = {}
        for p in portions:
            dtypes = [i.strip(', ;.') for i in p.split(' ') if i.strip(', ;.') in DAMAGETYPES]
            for d in dtypes:
                ret[d] = {'form':None,'damage_condition':[]}
                if len(p.split('(')) > 1 and p.endswith(')'):
                    if p.split('(')[1].lower().startswith('only when in') and 'form' in p.split('(')[1].lower():
                        if not p.split('(')[1].lower().split(' ')[3] in self.forms:
                            self.forms.append(p.split('(')[1].lower().split(' ')[3])
                        ret[d]['form'] = p.split('(')[1].lower().split(' ')[3]
                for mod in [' adamantine ',' silvered ',' magical ',' nonmagical ']:
                    if mod in p:
                        ret[d]['damage_condition'].append(mod.strip())
        return ret
    
    def _parse_atk(self,atk):
        ret = {
            'name':atk['name'],
            'form':None,
            'desc':atk['desc'].replace('<i>','').replace('</i>',''),
            'bonus':0,
            'damage':[],
            'type':'',
            'automated':False
        }

        if 'form only)' in ret['name'].lower():
            ret['form'] = ret['name'].split('(')[1].split(' ')[0].lower()
            ret['name'] = ret['name'].split('(')[0]
        
        try:
            ret['type'] = ret['desc'].split(': ')[0]
            ret['bonus'] = int(ret['desc'].split(': ')[1].split(', ')[0].split(' ')[0].strip('+'))

            hitparts = split_on(ret['desc'].lower().split('hit: ')[1],[', ',' and '])
            for hit in hitparts:
                damage = {}
                damage['average'] = int(hit.split(' ')[0])
                damage['roll'] = split_on(hit,['(',')'])[1].replace(' ','')
                typestr = split_on(hit,[' (',') '])[2].split(' ')[0]
                if typestr in DAMAGETYPES:
                    damage['type'] = typestr
                else:
                    damage['type'] = ''
                ret['damage'].append(damage)
            ret['automated'] =  True
        except: 
            pass
        
        return ret
    
    def _parse_spellcasting(self,string):
        ret = {
            'desc':string.replace('• ',''),
            'type':'',
            'dc':0,
            'bonus':0,
            'ability':'',
            'components':[],
            'spells':[],
            'slots':{},
            'automated':False
        }

        try:
            if 'innate' in ret['desc']:
                ret['type'] = 'innate'
            else:
                for i in CASTERS:
                    if i in ret['desc'].lower():
                        ret['type'] = i
                        break
            
            if '(' in ret['desc'] and ')' in ret['desc']:
                stats_str = split_on(ret['desc'],['(',')'])[1]
                if 'DC' in stats_str:
                    ret['dc'] = int(stats_str.split(', ')[0].split(' ')[3])
                if 'to hit' in stats_str:
                    ret['bonus'] = int(stats_str.split(', ')[1].split(' ')[0].strip('+'))

            for comp in ['material','somatic','verbal']:
                if not comp in ret['desc'].lower():
                    ret['components'].append(comp)
            
            lines = split_on(ret['desc'],['\n','\n\n'])[1:]
            for line in lines:
                if ret['type'] == 'innate' or ret['type'] == '':
                    per_day = line.split(': ')[0]
                    spells = split_on(line.split(': ')[1],[',',', '])
                    for spell in spells:
                        ret['spells'].append({'spell':spell,'per_day':per_day})
                else:
                    spells = split_on(line.split(': ')[1],[',',', '])
                    level = line.split(': ')[0].split(' (')[0]
                    slots = split_on(line,[' (','):'])[1]
                    if 'slot' in slots:
                        slots = int(slots.split(' ')[0])
                        ret['slots'][int(re.findall(r'[1-9]',level)[0])] = slots
                    for spell in spells:
                        if 'level' in level.lower():
                            ret['spells'].append({'spell':spell,'level':int(re.findall(r'[1-9]',level)[0]),'slots':slots})
                        else:
                            ret['spells'].append({'spell':spell,'level':level,'slots':slots})


            
            for ability in ABILITIES:
                if ability in ret['desc'].lower():
                    ret['ability'] = ability
            
            ret['automated'] = True
        except:
            pass

        return ret
    
    def to_dict(self):
        return {
            'name':self.name,
            'type':self.type,
            'alignment':self.alignment,
            'size':self.size,
            'hp':self.hp,
            'ac':self.ac,
            'forms':self.forms,
            'form':self.form,
            'form_name':self.forms[self.form],
            'cr':self.challenge,
            'cr_format':self.challenge_display,
            'prof':self.proficiency_bonus,
            'skills':self.skills,
            'abilities':self.abilities,
            'vuln':self.vuln,
            'resist':self.resist,
            'immune':self.immune,
            'condition_immune':self.condition_immunities,
            'special_abilities':self.special_abilities,
            'actions':self.actions,
            'legendary_actions':self.legendary_actions,
            'reactions':self.reactions,
            'spellcasting':self.spellcasting,
            'meta':{
                'slug':self.slug,
                'img':self.img
            }
        }
    
    def to_json(self,indent=None):
        return json.dumps(self.to_dict(),indent=indent)

    def setup(self):
        global SKILLS, DAMAGETYPES
        if self.options['rollhp']:
            self.hp = d20.roll(self.data['hit_dice']).total
        else:
            self.hp = int(self.data['hit_points'])

        self.forms = ['material']
        self.form = 0

        self.challenge = float(eval(self.data['challenge_rating']))
        self.challenge_display = self.data['challenge_rating']
        self.proficiency_bonus = self._get_proficiency()
        
        self.skills = {}
        for s in SKILLS.keys():
            if s in self.data['skills'].keys():
                self.skills[s] = self.data['skills'][s]+0
            else:
                self.skills[s] = getmod(self.data[SKILLS[s]])
        
        self.ac = self.data['armor_class']

        self.vuln = self._parse_dmg_string(self.data['damage_vulnerabilities'])
        self.resist = self._parse_dmg_string(self.data['damage_resistances'])
        self.immune = self._parse_dmg_string(self.data['damage_immunities'])

        self.condition_immunities = self.data['condition_immunities'].split(', ')

        self.actions = [self._parse_atk(atk) for atk in self.data['actions']]

        self.spellcasting = {}
        self.special_abilities = self.data['special_abilities'][:]
        for ability in self.data['special_abilities']:
            if 'spellcasting' in ability['name'].lower():
                self.spellcasting[ability['name']] = self._parse_spellcasting(ability['desc'])

        self.abilities = {}
        for ability in ABILITIES:
            if self.data[ability+'_save'] == None:
                save = getmod(self.data[ability])
            else:
                save = self.data[ability+'_save']
            self.abilities[ability] = {
                'score':self.data[ability],
                'modifier':getmod(self.data[ability]),
                'save':save
            }
        
        self.reactions = self.data['reactions'][:]
        self.legendary_actions = self.data['legendary_actions']

        self.slug = self.data['slug']
        self.name = self.data['name']
        self.img = self.data['img_main']
        self.size = self.data['size']
        self.type = self.data['type']
        self.alignment = self.data['alignment']

    def save(self,ability,advdis=''): #advdis = "adv" or "dis"
        additional = {
            'adv':'kh1',
            'dis':'kl1',
            '':''
        }[advdis]
        if self.abilities[ability]['save'] >= 0:
            return d20.roll('d20'+additional+'+'+str(self.abilities[ability]['save']))
        else:
            return d20.roll('d20'+additional+str(self.abilities[ability]['save']))
    
    def check(self,skill_or_ability,advdis=''): #advdis = "adv" or "dis"
        additional = {
            'adv':'kh1',
            'dis':'kl1',
            '':''
        }[advdis]
        if skill_or_ability in SKILLS.keys():
            if self.skills[skill_or_ability] >= 0:
                return d20.roll('d20'+additional+'+'+str(self.skills[skill_or_ability]))
            else:
                return d20.roll('d20'+additional+str(self.skills[skill_or_ability]))
        elif skill_or_ability in ABILITIES:
            if self.abilities[skill_or_ability]['modifier'] >= 0:
                return d20.roll('d20'+additional+'+'+str(self.abilities[skill_or_ability]['modifier']))
            else:
                return d20.roll('d20'+additional+str(self.abilities[skill_or_ability]['modifier']))

def get_gapi(path,scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']): # From https://developers.google.com/sheets/api/quickstart/python
    creds = service_account.Credentials.from_service_account_file(path, scopes=scopes)
    return build('sheets', 'v4', credentials=creds)



