import requests, json
from api.api_utils import *
import d20
import fractions
import urllib.parse

token = None
user_id = None

__all__ = ['get_critterdb']


class APIError(Exception):
    pass


def error(res):
    if res.status_code == 200 or res.status_code == 201:
        pass
    else:
        raise APIError('Error {}. The server returned the following message:\n'
                       '{}'.format(res.status_code, res.text))
    return res.json()


def _url(path):
    return 'https://critterdb.com/api' + path


# Creatures
def _get_creature(id):
    return error(requests.get(
        url=_url('/creatures/' + id)
    ))

# Bestiaries
def get_bestiary_creatures(id):
    return error(requests.get(
        url=_url('/bestiaries/' + id + '/creatures')
        ))

class CreatureCritter(Creature):
    def get_creature_info(self, kwargs):
        self.src = 'critterdb'
        if 'cid' in kwargs.keys():
            dat = _get_creature(kwargs['cid'])
        else:
            dat = kwargs['data']
        proc = json.loads(
            json.dumps(dat)
            .replace('<i>','')
            .replace('</i>','')
            .replace('<strong>','')
            .replace('</strong>','')
            .replace('non-magical','nonmagical')
        )
        return proc

    def _parse_atk(self,atk):
        ret = {
            'name':atk['name'],
            'form':None,
            'desc':atk['description'].replace('<i>','').replace('</i>',''),
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
                try:
                    damage = {}
                    damage['average'] = int(hit.split(' ')[0])
                    damage['roll'] = split_on(hit,['(',')'])[1].replace(' ','')
                    typestr = split_on(hit,[' (',') '])[2].split(' ')[0]
                    if typestr in DAMAGETYPES:
                        damage['type'] = typestr
                    else:
                        damage['type'] = ''
                    ret['damage'].append(damage)
                except:
                    pass
            ret['automated'] =  True
        except: 
            pass
        
        return ret

    def _parse_spellcasting_pc(self,string):
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

                    spells = []
                    spell_line = line.split(': ')[1]
                    jnr = ''
                    in_paran = 0
                    skip = False
                    for l in range(len(spell_line)):
                        if skip:
                            skip = False
                            continue
                        elif spell_line[l] == ',' and in_paran <= 0:
                            try:
                                if spell_line[l+1] == ' ':
                                    skip = True
                            except:
                                pass
                            spells.append(jnr.strip(','))
                            jnr = ''
                        if spell_line[l] == '(':
                            in_paran += 1
                            jnr += '('
                        elif spell_line[l] == ')':
                            in_paran -= 1
                            jnr += ')'
                        else:
                            jnr += spell_line[l]
                    if len(jnr) > 0:
                        spells.append(jnr.strip(','))

                    for spell in spells:
                        ret['spells'].append({'spell':spell,'per_day':per_day})
                else:
                    spells = []
                    spell_line = line.split(': ')[1]
                    jnr = ''
                    in_paran = 0
                    skip = False
                    for l in range(len(spell_line)):
                        if skip:
                            skip = False
                            continue
                        elif spell_line[l] == ',' and in_paran <= 0:
                            try:
                                if spell_line[l+1] == ' ':
                                    skip = True
                            except:
                                pass
                            spells.append(jnr.strip(','))
                            jnr = ''
                        if spell_line[l] == '(':
                            in_paran += 1
                            jnr += '('
                        elif spell_line[l] == ')':
                            in_paran -= 1
                            jnr += ')'
                        else:
                            jnr += spell_line[l]
                    if len(jnr) > 0:
                        spells.append(jnr.strip(','))

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
    
    def setup(self):
        stats = self.data['stats']

        if self.options['rollhp']:
            self.hp = d20.roll(
                str(stats['numHitDie'])
                +'d'+str(stats['hitDieSize'])
                +'+'+str(stats['numHitDie']*getmod(stats['abilityScores']['constitution']))
            ).total
        else:
            self.hp = int((stats['hitDieSize']+1) * 0.5*stats['numHitDie'] + stats['numHitDie'] * getmod(stats['abilityScores']['constitution']))

        self.forms = ['material']
        self.form = 0

        self.challenge = stats['challengeRating']
        self.challenge_display = str(fractions.Fraction(fractions.Decimal(self.challenge)))
        self.proficiency_bonus = stats['proficiencyBonus']

        self.skills = {}
        _skills = {}
        for s in stats['skills']:
            if 'value' in s.keys():
                _skills[s['name'].lower().replace(' ','_')] =  s['value']
            else:
                _skills[s['name'].lower().replace(' ','_')] = s['proficient']
        for s in SKILLS.keys():
            if s in _skills.keys():
                if type(_skills[s]) == int:
                    self.skills[s] = _skills[s]
                else:
                    if _skills[s]:
                        self.skills[s] = getmod(stats['abilityScores'][SKILLS[s]])+self.proficiency_bonus
                    else:
                        self.skills[s] = getmod(stats['abilityScores'][SKILLS[s]])
            else:
                self.skills[s] = getmod(stats['abilityScores'][SKILLS[s]])

        self.ac = stats['armorClass']

        self.resist = {}
        self.vuln = {}
        self.immune = {}
        _check = {'damageResistances':'resist','damageVulnerabilities':'vuln','damageImmunities':'immune',}
        for t in _check.keys():
            items = stats[t]
            for i in items:
                mods = []
                for j in ['nonmagical','magical','silvered','adamantine']:
                    if j in i.replace(',','').split(' '):
                        mods.append(j)
                for j in i.replace(',','').lower().split(' '):
                    if j in DAMAGETYPES:
                        getattr(self,_check[t])[j] = {
                            'form':None,
                            'damage_condition':mods
                        }

        self.condition_immunities = [i.lower() for i in stats['conditionImmunities']]

        self.actions = [self._parse_atk(atk) for atk in stats['actions']]

        self.spellcasting = {}
        self.special_abilities = stats['additionalAbilities'][:]
        for ability in stats['additionalAbilities']:
            if 'spellcasting' in ability['name'].lower():
                self.spellcasting[ability['name']] = self._parse_spellcasting_pc(ability['description'])
        
        self.abilities = {}
        saves = {}
        for s in stats['savingThrows']:
            if 'value' in s.keys():
                saves[s['ability']] = s['value']
                continue
            if s['proficient']:
                saves[s['ability']] = getmod(stats['abilityScores'][s['ability']])+self.proficiency_bonus
            else:
                saves[s['ability']] = getmod(stats['abilityScores'][s['ability']])
        for s in ABILITIES:
            if s in saves.keys():
                save = saves[s]
            else:
                save = getmod(stats['abilityScores'][s])
            self.abilities[s] = {
                'score':stats['abilityScores'][s],
                'modifier':getmod(stats['abilityScores'][s]),
                'save':save
            }

        self.reactions = stats['reactions']
        self.legendary_actions = stats['legendaryActions']
        
        self.name = self.data['name']
        self.slug = self.data['name'].lower()
        self.type = stats['race'].lower()
        self.alignment = stats['alignment'].lower()
        self.size = stats['size'].lower()
        self.img = self.data['flavor']['imageUrl']

def get_critterdb(url):
    try:
        path = urllib.parse.urlparse(url.replace('/#','')).path.split('/')[1:]
        if path[0] == 'creature':
            return CreatureCritter(cid=path[2])
        else:
            return [CreatureCritter(data=i) for i in get_bestiary_creatures(path[2])]
    except IndexError:
        raise ValueError('URL is invalid.')
    except:
        raise PermissionError('Creature or Bestiary cannot be accessed, it may not be shared or may not exist.')
