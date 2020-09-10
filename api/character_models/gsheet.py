from api.api_utils import *
from api.character_models.base import Character
import os
from googleapiclient.errors import HttpError
import re, json

API_ENGINE = get_gapi(os.path.join('lock','gapi.json'))
API_ACCT = 'xl30-778@lair3-289018.iam.gserviceaccount.com'

class GSheet(Character):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sheet_id = kwargs['sheet_id']

        self.service = API_ENGINE
        self.sheet_engine = self.service.spreadsheets()

        self.preload = {}

        try:
            self.sheet_engine.values().get(spreadsheetId=self.sheet_id,range='a1').execute()
        except HttpError as err:
            if err.resp.status == 404:
                raise ValueError('XL3 cannot access that sheet. Make sure it is readable by link sharing, or that it is shared with '+API_ACCT+' .')
        
        self.load_character()
    
    def get(self,r):
        if type(r) == list:
            ret = {}
            for rn in r:
                try:
                    ret[rn] = self.preload[rn]
                except KeyError:
                    raise KeyError('Range '+r+' has not been preloaded.')
            return ret
        else:
            try:
                return self.preload[r]
            except KeyError:
                raise KeyError('Range '+r+' has not been preloaded.')

    def preload_all(self,ranges):
        dat = self.sheet_engine.values().batchGet(spreadsheetId=self.sheet_id,ranges=ranges).execute().get('valueRanges',[])
        for r in range(len(ranges)):
            try:
                data = dat[r]['values']
                if len(data) > 0:
                    if len(data) > 1:
                        ret = []
                        for d in data:
                            if len(d) > 1:
                                ret.append(d)
                            else:
                                ret.append(d[0])
                        out = ret[:]
                    else:
                        if len(data[0]) > 1:
                            out = data[:]
                        else:
                            out = data[:][0][0]
                else:
                    out = data[:]

                self.preload[ranges[r]] = out
            except KeyError:
                self.preload[ranges[r]] = []
    
    def parse_attack(self,name,bonus,desc):
        ret = {
            'name':name,
            'bonus':bonus,
            'desc':desc,
            'damage':[],
            'properties':[],
            'automated':False
        }

        try:
            damagetypes = desc.split('|')[0].split(']+')
            for d in damagetypes:
                roll = split_on(d,['[',']'])[0]
                mods = []
                for t in split_on(d,['[',']'])[1].split(' '):
                    if t in ['magical','nonmagical','adamantine','silvered']:
                        mods.append(t)
                    elif t in DAMAGETYPES:
                        dtype = t
                    else:
                        pass
                ret['damage'].append({
                    'roll':roll,
                    'type':dtype,
                    'mods':mods
                })
            
            props = desc.split('\n')[1].split(', ')
            for prop in props:
                item = {
                    'name':prop.split(' ')[0]
                }
                if '(' in prop:
                    dat = split_on(prop,['(',')'])[1].split(' ')
                    try:
                        item[dat[0]] = dat[1]
                    except IndexError:
                        item['value'] = dat[0]
                ret['properties'].append(item)
            ret['automated'] = True
        except:
            pass
        return ret
        
    
    def load_character(self):
        all_ranges = [
            'c6','t7','t5','al6','ae7','h14','z12','aj28','r12','u16','v12','r32:r36','y32:y36','ac32:ac36','c15','c20',
            'c25','c30','c35','c40','i17:i22','i25:i42','i51','i52','i53','n96:n98','x96:x98','ah96:ah98','ak101','d100:d104',
            'n100:n104','x100:x104','e107','ak113','e119','ak124','e129','ak134','e138','ak142','n106:n110','x106:x110','ah106:ah110',
            'd112:d117','n112:n117','x112:x117','n118:n121','x118:x121','ah118:ah121','d123:d126','n123:n126','x123:x126',
            'n128:n131','x128:x131','ah128:ah131','d133:d135','n133:n135','x133:x135','n137:n139','x137:x139','ah137:ah139',
            'd141:d143','n141:n143','x141:x143','c91','u91','ab91','ai91'
            ]
        self.preload_all(all_ranges)

        # Base character info
        self.name = self.get('c6')
        self.race = self.get('t7')
        class_str = self.get('t5')
        self.class_display = class_str
        c = 0
        self.classes = []
        for i in class_str.split(' '):
            if c == 0:
                sub = i
            elif c == 1:
                _cls = i
            else:
                self.classes.append({
                    'class':_cls.lower(),
                    'subclass':sub.lower(),
                    'level':int(i)
                })
                c = 0
                continue
            c += 1
        self.player_level = int(self.get('al6'))
        self.xp = int(base10(self.get('ae7')))
        self.proficiency_bonus = int(self.get('h14'))
        self.speed = int(base10(self.get('z12')))
        self.alignment = self.get('aj28')

        # Combat stats
        self.ac = int(self.get('r12'))
        self.max_hp = int(self.get('u16'))
        self.hp = self.max_hp+0
        self.initiative = int(base10(self.get('v12')))

        ## Attacks
        atk_names = self.get('r32:r36')
        atk_bonuses = self.get('y32:y36')
        atk_descs = self.get('ac32:ac36')
        self.attacks = {}
        for a in range(len(atk_names)):
            self.attacks[atk_names[a]] = self.parse_attack(atk_names[a],int(atk_bonuses[a].strip('+')),atk_descs[a])
        
        # Scores, saves, and skills
        scores = [int(i) for i in self.get(['c15','c20','c25','c30','c35','c40']).values()]
        saves = [int(base10(i)) for i in self.get('i17:i22')]
        mods = [getmod(i) for i in scores]
        self.abilities = {}
        for a in range(len(ABILITIES)):
            self.abilities[ABILITIES[a]] = {
                'score':scores[a],
                'mod':mods[a],
                'save':saves[a]
            }
        self.skills = {}
        skillvals = [int(base10(i)) for i in self.get('i25:i42')]
        for s in range(len(list(SKILLS.keys()))):
            self.skills[list(SKILLS.keys())[s]] = skillvals[s]
        self.other_profs = {}
        for p in ['i51','i52','i53']:
            try:
                profs = self.get(p).split(', ')
                if len(profs) >= 1:
                    for i in profs:
                        if i != '': self.other_profs[alpha(i).lower()] = i
            except:
                pass
        
        # Spellcasting
        self.spellcasting = {}
        spcls = self.get('c91')
        if spcls != []:
            self.spellcasting[spcls] = {}
            self.spellcasting[spcls]['ability'] = self.get('u91')
            self.spellcasting[spcls]['save_dc'] = self.get('ab91')
            self.spellcasting[spcls]['attack_bonus'] = self.get('ai91')

            spelloc = {
                0:{
                    'ranges':['n96:n98','x96:x98','ah96:ah98']
                },
                1:{
                    'slots':'ak101',
                    'ranges':['d100:d104','n100:n104','x100:x104']
                },
                2:{
                    'slots':'e107',
                    'ranges':['n106:n110','x106:x110','ah106:ah110']
                },
                3:{
                    'slots':'ak113',
                    'ranges':['d112:d117','n112:n117','x112:x117']
                },
                4:{
                    'slots':'e119',
                    'ranges':['n118:n121','x118:x121','ah118:ah121']
                },
                5:{
                    'slots':'ak124',
                    'ranges':['d123:d126','n123:n126','x123:x126']
                },
                6:{
                    'slots':'e129',
                    'ranges':['n128:n131','x128:x131','ah128:ah131']
                },
                7:{
                    'slots':'ak134',
                    'ranges':['d133:d135','n133:n135','x133:x135']
                },
                8:{
                    'slots':'e138',
                    'ranges':['n137:n139','x137:x139','ah137:ah139']
                },
                9:{
                    'slots':'ak142',
                    'ranges':['d141:d143','n141:n143','x141:x143']
                },
            }

            self.spellcasting[spcls]['spells'] = {}
            for k in spelloc.keys():
                spells = []
                for r in spelloc[k]['ranges']:
                    spells.extend(self.get(r))
                if k > 0:
                    try:
                        slots = int(base10(self.get(spelloc[k]['slots'])))
                        self.spellcasting[spcls]['spells'][k] = {
                            'slots':slots,
                            'spells':spells
                        }
                    except:
                        self.spellcasting[spcls]['spells'][k] = {
                            'slots':0,
                            'spells':[]
                        }
                else:
                    self.spellcasting[spcls]['spells'][k] = {
                            'spells':spells
                        }
    
    def to_dict(self):
        items = [
            'name','race','class_display','classes','level','xp','prof','speed','alignment','ac','max_hp','hp','init','attacks','abilities','skills','other_profs','spellcasting'
            ]
        return {i:getattr(self,i,None) for i in items}

    def to_json(self,indent=None):
        return json.dumps(self.to_dict(),indent=indent)

sheet = GSheet(sheet_id='1aKNfgfVDxXygYfsmTkZvqF5ui_yjZ3y-ugLCB1Gh9ug') # Aadi
#sheet = GSheet(sheet_id='1Mmu8ZJ8EHccROYzFG4BrPSpLiIV4HD_BL_9cgdBc5Hw') # Ansh

with open('out.json','w') as f:
    f.write(sheet.to_json(indent=4))
        
