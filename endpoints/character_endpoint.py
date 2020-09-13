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
    405: {'model':SimpleResult,'description':'You must be logged in to view characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
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
    405: {'model':SimpleResult,'description':'You must be logged in to view characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
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
    405: {'model':SimpleResult,'description':'You must be logged in to view characters.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
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
        path = []
    else:
        prop = parts[0]
        path = parts[1:]
    if prop == 'id':
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'Cannot edit character ID.'}
    
    MODVAL = model.data
    
    try:
        cd = ('server.characters[charid].'+prop+'["'+'"]["'.join(path)+'"] = MODVAL').replace('[""]','')
        exec(cd,globals(),locals())
    except KeyError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Could not find the referenced property.'}
    except AttributeError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Could not find the referenced property.'}
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
    

    

    


