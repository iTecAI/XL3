from api.api_utils import *
from api.character_models.base import Character
import os
from googleapiclient.errors import HttpError
import re, json
from _runtime import server, CONFIG

API_ENGINE = get_gapi(os.path.join('lock','gapi.json'))
API_ACCT = CONFIG['CHARACTERS']['xl3_email']

class GSheet(Character):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sheet_id = kwargs['sheet_id']
        if 'init_load' in kwargs.keys():
            self.init_load = kwargs['init_load']
        else:
            self.init_load = True

        service = API_ENGINE
        sheet_engine = service.spreadsheets()

        self.preload = {}

        try:
            sheet_engine.values().get(spreadsheetId=self.sheet_id,range='a1').execute()
        except HttpError as err:
            if err.resp.status == 404:
                raise ValueError('XL3 cannot access that sheet. Make sure it is readable by link sharing, or that it is shared with '+API_ACCT+' .')
        
        self.load_character(sheet_engine)
    
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

    def preload_all(self,ranges,engine):
        dat = engine.values().batchGet(spreadsheetId=self.sheet_id,ranges=ranges).execute().get('valueRanges',[])
        for r in range(len(ranges)):
            try:
                data = dat[r]['values']
                if len(data) > 0:
                    if len(data) > 1:
                        ret = []
                        for d in data:
                            if len(d) > 1 or len(d) == 0:
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
                    out = ''


                self.preload[ranges[r]] = out
            except KeyError:
                self.preload[ranges[r]] = ''
    
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

    def map_adv(self,astr):
        if astr == 'adv':
            return '2d20kh1'
        if astr == 'dis':
            return '2d20kl1'
        return 'd20'
        
    
    def load_character(self,engine):
        all_ranges = [
            'c6','t7','t5','al6','ae7','h14','z12','aj28','r12','u16','v12','r32:r36','y32:y36','ac32:ac36','c15','c20',
            'c25','c30','c35','c40','i17:i22','i25:i42','i51','i52','i53','n96:n98','x96:x98','ah96:ah98','ak101','d100:d104',
            'n100:n104','x100:x104','e107','ak113','e119','ak124','e129','ak134','e138','ak142','n106:n110','x106:x110','ah106:ah110',
            'd112:d117','n112:n117','x112:x117','n118:n121','x118:x121','ah118:ah121','d123:d126','n123:n126','x123:x126',
            'n128:n131','x128:x131','ah128:ah131','d133:d135','n133:n135','x133:x135','n137:n139','x137:x139','ah137:ah139',
            'd141:d143','n141:n143','x141:x143','c91','u91','ab91','ai91','Additional!t69:t79','Additional!ab69:ab79','Additional!ai69:ai79','c176',
            'aj11','ae12:ae14','ae16:ae18','ae20:ae22','ae24:ae26','h11','r45:r56','ac45:ac56','r25','c148','f148','i148',
            'l148','c150','f150','i150','l150','r165:r177','c59:c84','p59:p84','ac59:ac84','i54','Inventory!d3','Inventory!d6','Inventory!d9',
            'Inventory!d12','Inventory!d15','Inventory!j3:j76','Inventory!aa3:aa76','Inventory!aq3:aq76','Inventory!ar3:ar76',
            'Inventory!as3:as76','Inventory!at3:at76','v15','c45','c16','c21','c26','c31','c36','c41','d16','d21','d26','d31','d36','d41',
            'h17:h22','h25:h42'
            ]
        all_ranges.extend(['p'+str(i) for i in range(17,23)])
        all_ranges.extend(['p'+str(i) for i in range(25,43)])

        all_ranges.extend(['Inventory!i'+str(i) for i in range(3,77)])
        all_ranges.extend(['Inventory!z'+str(i) for i in range(3,77)])
        self.preload_all(all_ranges,engine)

        # RP info
        self.background = self.get('aj11')
        self.traits = {
            'personality_traits':'\n'.join(self.get('ae12:ae14')),
            'ideals':'\n'.join(self.get('ae16:ae18')),
            'bonds':'\n'.join(self.get('ae20:ae22')),
            'flaws':'\n'.join(self.get('ae24:ae26'))
        }
        self.languages = self.get('r45:r56');
        self.physical = {
            'age':int(base10(self.get('c148'))),
            'height':self.get('f148'),
            'weight':self.get('i148'),
            'size':self.get('l148'),
            'gender':self.get('c150'),
            'eyes':self.get('f150'),
            'hair':self.get('i150'),
            'skin':self.get('i150'),
        }
        self.backstory = ' '.join(self.get('r165:r177')).replace('  ',' ')


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
        self.level = int(self.get('al6'))
        self.xp = int(base10(self.get('ae7')))
        self.proficiency_bonus = int(self.get('h14'))

        self.speed = {
            'walk':int(base10(self.get('z12')))
        }
        others = self.get('i54')
        if others != '-':
            for i in others.split(', '):
                parts = i.split(' ft. ')
                self.speed[parts[1].lower()] = int(base10(parts[0]))

        self.alignment = self.get('aj28')
        self.image = self.get('c176')
        if '✧' == self.get('h11'):
            self.inspiration = True
        else:
            self.inspiration = False
        self.equipped_items = self.get('ac45:ac56')
        self.death_saves = {
            'success':0,
            'fail':0
        }
        hd_raw = self.get('r25')
        self.hit_dice = {
            'raw':hd_raw,
            'die_size':int(base10(hd_raw.split('d')[1])),
            'max':int(base10(hd_raw.split('d')[0])),
            'current':int(base10(hd_raw.split('d')[0]))
        }
        self.passive_perception = int(base10(self.get('c45')))

        # Combat stats
        self.ac = int(self.get('r12'))
        self.max_hp = int(self.get('u16'))
        self.hp = self.max_hp+0
        self.thp = 0
        self.init = int(base10(self.get('v12')))
        self.init_adv = self.map_adv(self.get('v15'))

        ## Attacks
        atk_names = self.get('r32:r36')
        atk_bonuses = self.get('y32:y36')
        atk_descs = self.get('ac32:ac36')
        self.attacks = {}
        for a in range(len(atk_names)):
            self.attacks[atk_names[a]] = self.parse_attack(atk_names[a],int(atk_bonuses[a].strip('+')),atk_descs[a])
        
        # Scores, saves, and skills
        scores = [int(i) for i in self.get(['c15','c20','c25','c30','c35','c40']).values()]
        base_scores = [int(base10(i)) for i in self.get(['c16','c21','c26','c31','c36','c41']).values()]
        mod_scores = [int(base10(i)) for i in self.get(['d16','d21','d26','d31','d36','d41']).values()]
        saves = [int(base10(i)) for i in self.get('i17:i22')]
        mods = [getmod(i) for i in scores]
        advs = [self.map_adv(str(self.get('p'+str(i))).strip('[]')) for i in range(17,23)]
        profs = [i == '◉' for i in self.get('h17:h22')]
        self.abilities = {}
        for a in range(len(ABILITIES)):
            self.abilities[ABILITIES[a]] = {
                'score':scores[a],
                'mod':mods[a],
                'save':saves[a],
                'adv':advs[a],
                'base_score':base_scores[a],
                'mod_score':mod_scores[a],
                'racial_mod':int(scores[a] - mod_scores[a] - base_scores[a]),
                'proficient':profs[a]
            }
        self.skills = {}
        skillvals = [int(base10(i)) for i in self.get('i25:i42')]
        advs = [self.map_adv(str(self.get('p'+str(i))).strip('[]')) for i in range(25,43)]
        profs = [i == '◉' for i in self.get('h25:h42')]
        for s in range(len(list(SKILLS.keys()))):
            if skillvals[s] > self.abilities[SKILLS[list(SKILLS.keys())[s]]]['mod'] + self.proficiency_bonus:
                expert = True
            else:
                expert = False
            self.skills[list(SKILLS.keys())[s]] = {
                'value':skillvals[s],
                'adv':advs[s],
                'proficient':profs[s],
                'expert':expert
            }
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
        if spcls != '':
            self.spellcasting[spcls] = {}
            self.spellcasting[spcls]['ability'] = self.get('u91')
            self.spellcasting[spcls]['save_dc'] = int(base10(self.get('ab91')))
            self.spellcasting[spcls]['attack_bonus'] = int(base10(self.get('ai91')))

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
                        self.spellcasting[spcls]['spells'][int(k)] = {
                            'slots':slots,
                            'spells':spells
                        }
                    except:
                        self.spellcasting[spcls]['spells'][int(k)] = {
                            'slots':0,
                            'spells':[]
                        }
                else:
                    self.spellcasting[spcls]['spells'][int(k)] = {
                            'spells':spells
                        }
            
        rlist = {'resist':'Additional!t69:t79','immune':'Additional!ab69:ab79','vuln':'Additional!ai69:ai79'}
        self.resist = {}
        self.vuln = {}
        self.immune = {}
        for k in rlist.keys():
            dat = self.get(rlist[k])
            for i in dat:
                if i == []:
                    continue
                item = {
                    'damage_condition':[]
                }
                parts = i.split(' ')
                for part in parts:
                    if part in ['magical','nonmagical','adamantine','silvered']:
                        item['damage_condition'].append(part)
                    elif part in DAMAGETYPES:
                        getattr(self,k)[part] = item
                        break
        
        # Other
        self.features = []
        self.features.extend(self.get('c59:c84'))
        self.features.extend(self.get('p59:p84'))
        self.features.extend(self.get('ac59:ac84'))

        if not self.init_load:
            return

        # Inventory
        self.inventory = {
            'carry_capacity':self.abilities['strength']['score']*15,
            'variant_encumbrance':{
                'encumbered':self.abilities['strength']['score']*5,
                'heavily_encumbered':self.abilities['strength']['score']*10
            },
            'current_weight':0,
            'containers':[
                {
                    'name':'inventory',
                    'apply_weight':True,
                    'removable':False,
                    'max_weight':self.abilities['strength']['score']*15,
                    'current_weight':0,
                    'coin_container':True,
                    'items':[]
                }
            ],
            'coin':[
                {
                    'name':'cp',
                    'conversion':0.01,
                    'amount':int(base10(self.get('Inventory!d3'))),
                    'weight':0.02
                },
                {
                    'name':'sp',
                    'conversion':0.1,
                    'amount':int(base10(self.get('Inventory!d6'))),
                    'weight':0.02
                },
                {
                    'name':'ep',
                    'conversion':0.5,
                    'amount':int(base10(self.get('Inventory!d9'))),
                    'weight':0.02
                },
                {
                    'name':'gp',
                    'conversion':1,
                    'amount':int(base10(self.get('Inventory!d12'))),
                    'weight':0.02
                },
                {
                    'name':'pp',
                    'conversion':10,
                    'amount':int(base10(self.get('Inventory!d15'))),
                    'weight':0.02
                },
            ]
        }

        # First column
        items = self.get('Inventory!j3:j76')
        qt = [int(base10(self.get('Inventory!i'+str(i)))) for i in range(3,77)]
        cost = [float(i) for i in self.get('Inventory!aq3:aq76')]
        wt = [float(i.split(' ')[0]) for i in self.get('Inventory!ar3:ar76')]
        for i in range(len(items)):
            if qt[i] < 1:
                self.inventory['containers'][0]['items'].append({
                    'name':items[i],
                    'quantity':0,
                    'cost':cost[i],
                    'weight':wt[i]
                })
            else:
                self.inventory['containers'][0]['items'].append({
                    'name':items[i],
                    'quantity':qt[i],
                    'cost':cost[i]/qt[i],
                    'weight':wt[i]/qt[i]
                })
        # Second column
        items = self.get('Inventory!aa3:aa76')
        qt = [int(base10(self.get('Inventory!z'+str(i)))) for i in range(3,77)]
        cost = [float(i) for i in self.get('Inventory!as3:as76')]
        wt = [float(i.split(' ')[0]) for i in self.get('Inventory!at3:at76')]
        for i in range(len(items)):
            if qt[i] < 1:
                self.inventory['containers'][0]['items'].append({
                    'name':items[i],
                    'quantity':0,
                    'cost':cost[i],
                    'weight':wt[i]
                })
            else:
                self.inventory['containers'][0]['items'].append({
                    'name':items[i],
                    'quantity':qt[i],
                    'cost':cost[i]/qt[i],
                    'weight':wt[i]/qt[i]
                })
        
        self.inventory_calculate()


        
