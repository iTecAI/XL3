from fastapi import APIRouter, status, Request, Response
from util import *
from classes import *
from _runtime import server, CONFIG
import logging, random, hashlib
from pydantic import BaseModel
from models import *
from _api import *
import os, pickle
from urllib.parse import urlparse
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
            if server.characters[char].owner == None:
                server.characters[char].owner = server.connections[fp].user.uid
            return True
        else:
            if char in server.characters.keys():
                return server.characters[char].options['public']
            else:
                with open(os.path.join('database','characters','registry.json'),'r') as f:
                    reg = json.load(f)
                    if char in reg.keys():
                        if reg[char]['public']:
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
            except SystemExit:
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
        'data':{i:'some data' for i in [
            'name','race','class_display','classes','level','xp','prof','speed',
            'alignment','ac','max_hp','hp','init','attacks','abilities','skills',
            'other_profs','spellcasting','resist','vuln','immune'
            ]}
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
async def new_character(fingerprint: str, model: NewCharacterModel, response=Response):
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


