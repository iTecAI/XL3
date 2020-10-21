from fastapi import APIRouter, status, Request, Response
from util import *
from classes import *
from _runtime import server, CONFIG
import logging, random, hashlib
from pydantic import BaseModel
from models import *
from _api import *
import os, pickle, time
from urllib.parse import urlparse
import re
logger = logging.getLogger("uvicorn.error")

def case(condition,t,f):
    if condition: return t
    else: return f

def get_proficiency(level):
    profs = {
        4:2,
        8:3,
        12:4,
        16:5,
        20:6
    }

    for p in profs.keys():
        if level <= p:
            return profs[p]

def has_class(cid,_cls,lvl,subc=None):
    for c in server.characters[cid].classes:
        if _cls == c['class'] and (subc == c['class'] or subc == None) and c['level'] >= lvl:
            return True
    return False
            

def recalculate(cid):
    # Misc stats
    server.characters[cid].proficiency_bonus = get_proficiency(server.characters[cid].level)

    # reload abilities
    for a in server.characters[cid].abilities.keys():
        server.characters[cid].abilities[a]['score'] = server.characters[cid].abilities[a]['base_score']+server.characters[cid].abilities[a]['mod_score'] + server.characters[cid].abilities[a]['racial_mod']
        server.characters[cid].abilities[a]['mod'] = getmod(server.characters[cid].abilities[a]['score'])
        server.characters[cid].abilities[a]['save'] = server.characters[cid].abilities[a]['mod'] + case(server.characters[cid].abilities[a]['proficient'],server.characters[cid].proficiency_bonus,0)

    for s in server.characters[cid].skills.keys():
        server.characters[cid].skills[s]['value'] = sum([
            server.characters[cid].abilities[SKILLS[s]]['mod'],
            case(server.characters[cid].skills[s]['proficient'],server.characters[cid].proficiency_bonus,0),
            case(server.characters[cid].skills[s]['expert'] and server.characters[cid].skills[s]['proficient'],server.characters[cid].proficiency_bonus,0),
            case(
                ('jack of all trades' in [x.lower() for x in server.characters[cid].features] or has_class(cid,'bard',2)) and not (server.characters[cid].skills[s]['expert'] and server.characters[cid].skills[s]['proficient']) and not server.characters[cid].skills[s]['proficient'],
                int(server.characters[cid].proficiency_bonus * 0.5),
                0
            )
        ])
    server.characters[cid].passive_perception = sum([
        10+server.characters[cid].skills['perception']['value'],
        case(server.characters[cid].skills['perception']['adv'] == '2d20kh1',5,0),
        case(server.characters[cid].skills['perception']['adv'] == '2d20kl1',-5,0),
        case(
            'feat: observant' in [x.lower() for x in server.characters[cid].features],
            5,0
        )
    ])
    server.characters[cid].init = sum([
        server.characters[cid].abilities['dexterity']['mod'],
        case(
            'jack of all trades' in [x.lower() for x in server.characters[cid].features] or has_class(cid,'bard',2),
            int(server.characters[cid].proficiency_bonus * 0.5),
            0
        ),
        case(
            'feat: alert' in [x.lower() for x in server.characters[cid].features],
            5,0
        )
    ])
    if not server.characters[cid].options['roll_hp']:
        hp_sum = 0
        first = True
        for i in server.characters[cid].hit_dice:
            for x in range(i['max']):
                if first:
                    first = False
                    continue
                hp_sum += round(i['die_size'] / 2) + 1 + server.characters[cid].abilities['constitution']['mod']
        server.characters[cid].max_hp = hp_sum+i['die_size']+server.characters[cid].abilities['constitution']['mod']

    server.characters[cid].inventory_calculate()

    # Recalculate spell slots
    mcs_level = 0
    sp_types = set()
    for i in server.characters[cid].classes:
        if i['class'].lower() in ['bard','cleric','druid','sorcerer','wizard']:
            mcs_level+=i['level']
            sp_types.add('full caster')
        if i['class'].lower() in ['paladin','ranger']:
            mcs_level+=int(i['level']/2)
            sp_types.add('half caster')
        if i['class'].lower() in ['rogue','fighter'] and i['subclass'] in ['arcane trickster','eldritch knight']:
            mcs_level+=int(i['level']/3)
            sp_types.add('third caster')
        if i['class'].lower() == 'artificer':
            mcs_level+=int(i['level']/2)
            sp_types.add('artificer casting')
    with open(os.path.join('api','static_data','spellcasting.json'),'r') as f:
        sps_data = json.load(f)

    sp_types = list(sp_types)
    if len(sp_types) == 1:
        c = 0
        for i in sps_data[sp_types[0]][mcs_level-1]['spells']:
            server.characters[cid].spell_slots[c]['total'] = i
            if server.characters[cid].spell_slots[c]['current'] > i:
                server.characters[cid].spell_slots[c]['current'] = i
            c+=1
    if len(sp_types) > 1:
        server.characters[cid].spell_slots = [{'total':i,'current':i} for i in sps_data['multiclass'][mcs_level-1]['spells']]
        c = 0
        for i in sps_data['multiclass'][mcs_level-1]['spells']:
            server.characters[cid].spell_slots[c]['total'] = i
            if server.characters[cid].spell_slots[c]['current'] > i:
                server.characters[cid].spell_slots[c]['current'] = i
            c+=1

def decache(cid):
    with open(os.path.join('database','characters','registry.json'),'r') as f:
        reg = json.load(f)
    if cid in reg.keys() and os.path.exists(os.path.join('database','characters',cid+'.pkl')):
        with open(os.path.join('database','characters',cid+'.pkl'),'rb') as f:
            server.characters[cid] = pickle.load(f)
    else:
        if not os.path.exists(os.path.join('database','characters',cid+'.pkl')) and cid in reg.keys():
            del reg[cid]
            with open(os.path.join('database','characters','registry.json'),'w') as f:
                json.dump(reg,f)
        raise ValueError('Character with ID '+cid+' does not exist.')

router = APIRouter()

def check_access(fp,char):
    try:
        if char in server.connections[fp].user.owned_characters:
            decache(char)
            if server.characters[char].owner == None:
                server.characters[char].owner = server.connections[fp].user.uid
            return True
        else:
            if char in server.characters.keys():
                return server.characters[char].options['public'] or server.characters[char].owner == server.connections[fp].user.uid
            else:
                with open(os.path.join('database','characters','registry.json'),'r') as f:
                    reg = json.load(f)
                    if char in reg.keys():
                        if reg[char]['public']:
                            return True
                        elif reg[char]['owner'] == server.connections[fp].user.uid:
                            decache(char)
                            return True
                        else:
                            return False
                    else:
                        return False
    except KeyError:
        return False

@router.get('/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to view characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MultipleCharacterResponseModel,'description':'Returns character data.','content':{'application/json':{'example':{
        'result':'Success.',
        'characters':[]
    }}}}
})
async def get_all_characters(fingerprint: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    
    characters = []
    to_remove = []
    for char in server.connections[fingerprint].user.owned_characters:
        if char in server.characters.keys():
            characters.append({
                'cid':char,
                'owner':server.characters[char].owner,
                'campaign':server.characters[char].campaign,
                'public':server.characters[char].options['public'],
                'data':server.characters[char].to_dict()
            })
        else:
            try:
                decache(char)
                characters.append({
                    'cid':char,
                    'owner':server.characters[char].owner,
                    'campaign':server.characters[char].campaign,
                    'public':server.characters[char].options['public'],
                    'data':server.characters[char].to_dict()
                })
            except ValueError:
                to_remove.append(char)
    for t in to_remove:
        server.connections[fingerprint].user.owned_characters.remove(t)
    return {
        'result':'Success.',
        'characters':characters
    }       


@router.get('/{charid}/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to view characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Returns character data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def get_character(fingerprint: str, charid: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    
    if charid in server.characters.keys():
        return {
            'result':'Success.',
            'cid':charid,
            'owner':server.characters[charid].owner,
            'campaign':server.characters[charid].campaign,
            'public':server.characters[charid].options['public'],
            'data':server.characters[charid].to_dict()
        }
    else:
        try:
            decache(charid)
            return {
                'result':'Success.',
                'cid':charid,
                'owner':server.characters[charid].owner,
                'campaign':server.characters[charid].campaign,
                'public':server.characters[charid].options['public'],
                'data':server.characters[charid].to_dict()
            }
        except ValueError:
            response.status_code = status.HTTP_403_FORBIDDEN
            return {'result':'You do not own this character.'}
    
@router.post('/new/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create characters.','content':{'application/json':{'example':{'result':'You must be logged in to create characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You have reached the maximum allowed characters.','content':{'application/json':{'example':{'result':'You have reached the maximum allowed characters.'}}}},
    400: {'model':SimpleResult,'description':'The submitted URL was incorrect.','content':{'application/json':{'example':{'result':'The submitted URL was incorrect.'}}}},
    200: {'model':NewCharacterResponseModel,'description':'Success. Character is created and assigned.','content':{'application/json':{'example':{'result':'Success.','cid':'Character ID'}}}}
})
async def new_character(fingerprint: str, model: NewCharacterModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create characters.'}
    if len(server.connections[fingerprint].user.owned_characters) >= int(CONFIG['CHARACTERS']['max_characters']):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You have reached the maximum allowed characters.'}
    if not urlparse(model.url).netloc in CONFIG['CHARACTERS']['domains'].split('|'):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {'result':'The submitted URL was incorrect. It should come from one of the following domains: '+', '.join(CONFIG['CHARACTERS']['domains'].split('|'))}
    if urlparse(model.url).netloc == 'docs.google.com':
        try:
            sheet = GSheet(sheet_id=urlparse(model.url).path.split('/')[1:][2])
        except ValueError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {'result':'The submitted URL was incorrect. Make sure it is readable by link sharing, or that it is shared with '+CONFIG['CHARACTERS']['xl3_email']+' .'}
        server.characters[sheet.id] = sheet
        sheet.owner = server.connections[fingerprint].user.uid
        sheet.cache()
        sheet.update()
        server.connections[fingerprint].user.owned_characters.append(sheet.id)
        server.connections[fingerprint].user.update()
        return {'result':'Success.','cid':sheet.id}

# Character actions
@router.post('/{charid}/duplicate/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to duplicate characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Returns duplicated character data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def dupe_character(fingerprint: str, charid: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    if len(server.connections[fingerprint].user.owned_characters) >= int(CONFIG['CHARACTERS']['max_characters']):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You have reached the maximum allowed characters.'}
    
    if charid in server.characters.keys():
        character_data = server.characters[charid].to_dict()
    else:
        try:
            decache(charid)
            character_data = server.characters[charid].to_dict()
        except ValueError:
            response.status_code = status.HTTP_403_FORBIDDEN
            return {'result':'You do not own this character.'}
    character_data['id'] = hashlib.sha256(str(int(time.time())+random.random()).encode('utf-8')).hexdigest()
    character_data['campaign'] = ''
    if ' copy_' in character_data['name']:
        pname = character_data['name'][:re.search(r' copy_[0-9]+$',character_data['name']).span()[0]]
    else:
        pname = character_data['name']

    c = 1
    while True:
        character_data['name'] = pname+' copy_'+str(c)
        found = False
        for i in server.connections[fingerprint].user.owned_characters:
            if server.characters[i].name == character_data['name']:
                found = True
        if not found:
            break
        c+=1
    charid = character_data['id']
    server.characters[charid] = Character.from_dict(character_data)
    server.characters[charid].update()
    server.characters[charid].cache()
    server.connections[fingerprint].user.update()
    server.connections[fingerprint].user.owned_characters.append(charid)
    return {
            'result':'Success.',
            'cid':charid,
            'owner':server.characters[charid].owner,
            'campaign':server.characters[charid].campaign,
            'public':server.characters[charid].options['public'],
            'data':server.characters[charid].to_dict()
        }

@router.post('/{charid}/delete/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to delete characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SimpleResult,'description':'Deletes character','content':{'application/json':{'example':{'result':'Success.'}}}}
})
async def delete_character(fingerprint: str, charid: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    if len(server.connections[fingerprint].user.owned_characters) >= int(CONFIG['CHARACTERS']['max_characters']):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You have reached the maximum allowed characters.'}
    
    if charid in server.characters.keys():
        del server.characters[charid]
    with open(os.path.join('database','characters','registry.json'),'r') as f:
        reg = json.load(f)
    if charid in reg.keys():
        del reg[charid]
    if os.path.exists(os.path.join('database','characters',charid+'.pkl')):
        os.remove(os.path.join('database','characters',charid+'.pkl'))
    with open(os.path.join('database','characters','registry.json'),'w') as f:
        json.dump(reg,f)
    server.connections[fingerprint].user.owned_characters.remove(charid)
    server.connections[fingerprint].char_update.update()
    server.connections[fingerprint].user.update()
    return {'result':'Success.'}

@router.post('/{charid}/modify/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection or Character Property not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Modifies character, then returns data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def modify_character(fingerprint: str, charid: str, model: ModCharModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    if len(server.connections[fingerprint].user.owned_characters) >= int(CONFIG['CHARACTERS']['max_characters']):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You have reached the maximum allowed characters.'}
    
    if charid in server.characters.keys():
        pass
    else:
        try:
            decache(charid)
        except ValueError:
            response.status_code = status.HTTP_403_FORBIDDEN
            return {'result':'You do not own this character.'}
    
    parts = model.path.split('.')
    if len(parts) == 1:
        prop = parts[0]
        _path = []
    else:
        prop = parts[0]
        _path = parts[1:]
    if prop == 'id':
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'Cannot edit character ID.'}
    
    MODVAL = model.data

    path = ''
    for p in _path:
        try:
            path += '['+str(int(p))+']'
        except ValueError:
            path += '["'+p+'"]'
    
    try:
        cd = 'server.characters[charid].'+prop+path+' = MODVAL'
        exec(cd,globals(),locals())
    except KeyError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Could not find the referenced property.'}
    except AttributeError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Could not find the referenced property.'}
    recalculate(charid)
    server.characters[charid].update()
    server.characters[charid].cache()
    server.connections[fingerprint].user.update()
    return {
        'result':'Success.',
        'cid':charid,
        'owner':server.characters[charid].owner,
        'campaign':server.characters[charid].campaign,
        'public':server.characters[charid].options['public'],
        'data':server.characters[charid].to_dict()
    }

@router.post('/{charid}/reset/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to view characters, or the Character was not directly loaded from Google Sheets.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Modifies character, then returns data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def reset_character(fingerprint: str, charid: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    if not hasattr(server.characters[charid],'sheet_id'):
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'Cannot reset character, as it was not loaded directly from Google Sheets.'}
    sid = server.characters[charid].sheet_id
    pre_cid = server.characters[charid].id
    pre_opts = server.characters[charid].options
    pre_inv = server.characters[charid].inventory
    server.characters[charid] =  GSheet(sheet_id=sid)
    server.characters[charid].id = pre_cid
    server.characters[charid].options = pre_opts
    #server.characters[charid].inventory = pre_inv
    
    server.characters[charid].update()
    server.characters[charid].cache()
    server.connections[fingerprint].user.update()
    return {
        'result':'Success.',
        'cid':charid,
        'owner':server.characters[charid].owner,
        'campaign':server.characters[charid].campaign,
        'public':server.characters[charid].options['public'],
        'data':server.characters[charid].to_dict()
    }

@router.post('/{charid}/modify/attacks/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify characters or passed Action was invalid.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection or Character Property not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Modifies character, then returns data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def char_atk_modify(fingerprint: str, charid: str, model: AtkModModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    if not model.action in ['add','remove','modify']:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'Invalid action.'}
    
    if model.action == 'add':
        try:
            new_atk = {
                'name':model.data['name'],
                'desc':'',
                'bonus':0,
                'bonus_mod':model.data['bonus_mod'],
                'damage':[],
                'properties':[],
                'category':model.data['category'],
                'type':model.data['type'],
                'maximize_damage':model.data['maxdmg'],
                'automated':True
            }

            for p in model.data['properties']:
                if p == '':
                    continue
                try:
                    p_dict = {}
                    parts = split_on(p,[' (',')'])
                    p_dict['name'] = parts[0]
                    if len(parts) > 1:
                        if len(parts[1].split(' ')) == 1:
                            p_dict['value'] = parts[1]
                        else:
                            p_dict[parts[1].split(' ')[0]] = parts[1].split(' ')[1]
                    new_atk['properties'].append(p_dict)
                except:
                    new_atk['automated'] = False
            
            new_atk['bonus'] = case(
                model.data['type'] == 'ranged' or (any([x['name'].lower().strip(' .,') == 'finesse' for x in new_atk['properties']]) and server.characters[charid].abilities['dexterity']['mod'] >= server.characters[charid].abilities['strength']['mod']),
                server.characters[charid].abilities['dexterity']['mod'],
                server.characters[charid].abilities['strength']['mod']
            ) + case(
                model.data['category'].lower()+' weapons' in server.characters[charid].weapon_profs or any([x.lower() in model.data['name'].lower() for x in server.characters[charid].weapon_profs]),
                server.characters[charid].proficiency_bonus,
                0
            )

            for d in model.data['damage']:
                if d == '':
                    continue
                try:
                    d_dict = {
                        'mods':[]
                    }
                    items = d.split(' ')
                    d_dict['roll'] = items.pop(0)
                    for it in items:
                        if it in DAMAGETYPES:
                            d_dict['type'] = it
                        if it in ['magical','adamantine','silvered','nonmagical']:
                            d_dict['mods'].append(it)
                    new_atk['damage'].append(d_dict)
                except:
                    new_atk['automated'] = False
            
            
            
            new_atk['desc'] = model.data['type']+' '+model.data['category']+' weapon attack. *To Hit:* '+case(new_atk['bonus']+new_atk['bonus_mod'] >= 0,'+','')+str(new_atk['bonus']+new_atk['bonus_mod'])+' *Hit:* '+' plus '.join([n+' damage' for n in model.data['damage']])+'\n'+', '.join(model.data['properties'])
            server.characters[charid].attacks.append(new_atk)

        except KeyError:
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {'result':'Bad data format.'}
    
    elif model.action == 'remove':
        if 'index' in model.data.keys():
            try:
                del server.characters[charid].attacks[model.data['index']]
            except IndexError:
                response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
                return {'result':'Index out of range.'}
        else:
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {'result':'Bad data format.'}
    elif model.action == 'modify':
        try:
            new_atk = {
                'name':model.data['name'],
                'desc':'',
                'bonus':0,
                'bonus_mod':model.data['bonus_mod'],
                'damage':[],
                'properties':[],
                'category':model.data['category'],
                'type':model.data['type'],
                'maximize_damage':model.data['maxdmg'],
                'automated':True
            }

            for p in model.data['properties']:
                if p == '':
                    continue
                try:
                    p_dict = {}
                    parts = split_on(p,[' (',')'])
                    p_dict['name'] = parts[0]
                    if len(parts) > 1:
                        if len(parts[1].split(' ')) == 1:
                            p_dict['value'] = parts[1]
                        else:
                            p_dict[parts[1].split(' ')[0]] = parts[1].split(' ')[1]
                    new_atk['properties'].append(p_dict)
                except:
                    new_atk['automated'] = False
            
            new_atk['bonus'] = case(
                model.data['type'] == 'ranged' or (any([x['name'].lower().strip(' .,') == 'finesse' for x in new_atk['properties']]) and server.characters[charid].abilities['dexterity']['mod'] >= server.characters[charid].abilities['strength']['mod']),
                server.characters[charid].abilities['dexterity']['mod'],
                server.characters[charid].abilities['strength']['mod']
            ) + case(
                model.data['category'].lower()+' weapons' in server.characters[charid].weapon_profs or any([x.lower() in model.data['name'].lower() for x in server.characters[charid].weapon_profs]),
                server.characters[charid].proficiency_bonus,
                0
            )

            for d in model.data['damage']:
                if d == '':
                    continue
                try:
                    d_dict = {
                        'mods':[]
                    }
                    items = d.split(' ')
                    d_dict['roll'] = items.pop(0)
                    for it in items:
                        if it in DAMAGETYPES:
                            d_dict['type'] = it
                        if it in ['magical','adamantine','silvered','nonmagical']:
                            d_dict['mods'].append(it)
                    new_atk['damage'].append(d_dict)
                except:
                    new_atk['automated'] = False
            
            
            
            new_atk['desc'] = model.data['type']+' '+model.data['category']+' weapon attack. *To Hit:* '+case(new_atk['bonus']+new_atk['bonus_mod'] >= 0,'+','')+str(new_atk['bonus']+new_atk['bonus_mod'])+' *Hit:* '+' plus '.join([n+' damage' for n in model.data['damage']])+'\n'+', '.join(model.data['properties'])
            server.characters[charid].attacks[model.data['index']] = new_atk

        except KeyError:
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {'result':'Bad data format.'}
        except IndexError:
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {'result':'Bad data format.'}

    recalculate(charid)
    server.characters[charid].update()
    server.characters[charid].cache()
    server.connections[fingerprint].user.update()

    return {
        'result':'Success.',
        'cid':charid,
        'owner':server.characters[charid].owner,
        'campaign':server.characters[charid].campaign,
        'public':server.characters[charid].options['public'],
        'data':server.characters[charid].to_dict()
    }

@router.post('/{charid}/modify/inventory/containers/new',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Modifies character inventory, then returns data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def inv_new_container(fingerprint: str, charid: str, model: NewContainerModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    
    server.characters[charid].inventory['containers'].append({
        'apply_weight':True,
        'coin_container':False,
        'current_weight':0,
        'items':[],
        'max_weight':0,
        'name':model.name.lower(),
        'removable':True
    })
    recalculate(charid)
    server.characters[charid].update()
    server.characters[charid].cache()
    server.connections[fingerprint].user.update()

    return {
        'result':'Success.',
        'cid':charid,
        'owner':server.characters[charid].owner,
        'campaign':server.characters[charid].campaign,
        'public':server.characters[charid].options['public'],
        'data':server.characters[charid].to_dict()
    }

@router.post('/{charid}/modify/inventory/containers/remove',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection or Container not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Modifies character inventory, then returns data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def inv_rem_container(fingerprint: str, charid: str, model: RemContainerModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    
    try:
        if not server.characters[charid].inventory['containers'][model.index]['removable']:
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {'result':'Container is not removable.'}
        del server.characters[charid].inventory['containers'][model.index]
    except IndexError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Container index not found.'}
    recalculate(charid)
    server.characters[charid].inventory['current_container'] = 'inventory'
    server.characters[charid].update()
    server.characters[charid].cache()
    server.connections[fingerprint].user.update()

    return {
        'result':'Success.',
        'cid':charid,
        'owner':server.characters[charid].owner,
        'campaign':server.characters[charid].campaign,
        'public':server.characters[charid].options['public'],
        'data':server.characters[charid].to_dict()
    }

@router.post('/{charid}/modify/inventory/items/new',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Modifies character inventory, then returns data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def inv_new_item(fingerprint: str, charid: str, model: NewItemModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}

    _weapons = {i['slug']:i for i in get5e('weapons')}
    _armor = {i['slug']:i for i in get5e('armor')}

    slug = model.name.lower().replace(' ','-').replace('\'','').replace('"','').replace('.','')
    item_type = 'gear'
    for i in list(_weapons.keys()):
        if _weapons[i]['slug'] == slug:
            item_type='weapon'
    for i in list(_armor.keys()):
        if _armor[i]['slug'] == slug:
            item_type='armor'

    try:
        server.characters[charid].inventory['containers'][model.containerIndex]['items'].append({
            'name':model.name,
            'quantity':model.quantity,
            'cost':model.cost,
            'weight':model.weight,
            'slug':slug,
            'type':item_type
        })
    except IndexError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Container index not found.'}
    
    recalculate(charid)
    server.characters[charid].update()
    server.characters[charid].cache()
    server.connections[fingerprint].user.update()

    return {
        'result':'Success.',
        'cid':charid,
        'owner':server.characters[charid].owner,
        'campaign':server.characters[charid].campaign,
        'public':server.characters[charid].options['public'],
        'data':server.characters[charid].to_dict()
    }

@router.post('/{charid}/modify/inventory/items/move',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'You do not own this character.','content':{'application/json':{'example':{'result':'You do not own this character.'}}}},
    200: {'model':SingleCharacterResponseModel,'description':'Modifies character inventory, then returns data.','content':{'application/json':{'example':{
        'result':'Success.',
        'cid':'character id',
        'owner':'fingerprint',
        'campaign':'campaign id, if any',
        'public':True,
        'data':{i:'some data' for i in ITEMS}
    }}}}
})
async def inv_mv_item(fingerprint: str, charid: str, model: MoveItemModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view characters.'}
    if not check_access(fingerprint,charid):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this character.'}
    
    try:
        server.characters[charid].inventory['containers'][model.newContainerIndex]['items'].append(
            server.characters[charid].inventory['containers'][model.oldContainerIndex]['items'][model.itemIndex]
        )
        del server.characters[charid].inventory['containers'][model.oldContainerIndex]['items'][model.itemIndex]
    except IndexError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Container or Item index not found.'}
    
    recalculate(charid)
    server.characters[charid].update()
    server.characters[charid].cache()
    server.connections[fingerprint].user.update()

    return {
        'result':'Success.',
        'cid':charid,
        'owner':server.characters[charid].owner,
        'campaign':server.characters[charid].campaign,
        'public':server.characters[charid].options['public'],
        'data':server.characters[charid].to_dict()
    }