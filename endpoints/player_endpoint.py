from re import search
from endpoints.character_endpoint import decache
from fastapi import APIRouter, status, Request, Response
from fastapi.responses import FileResponse
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
router = APIRouter()

def check_access(fp,cid,map):
    with open(os.path.join('database','campaigns','registry.json'),'r') as f:
        reg = json.load(f)
    for i in reg.keys():
        if i in server.connections[fp].user.owned_campaigns or i in server.connections[fp].user.participating_campaigns:
            with open(os.path.join('database','campaigns',i+'.pkl'),'rb') as f:
                server.campaigns[i] = pickle.load(f)
    if cid in reg.keys() and cid in server.campaigns.keys():
        with open(os.path.join('database','campaigns',cid+'.pkl'),'rb') as f:
            server.campaigns[cid] = pickle.load(f)
        if cid in server.connections[fp].user.owned_campaigns or cid in server.connections[fp].user.participating_campaigns:
            return map in server.campaigns[cid].maps.keys()
        return False
    else:
        return False

@router.get('/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to view maps.','content':{'application/json':{'example':{'result':'You must be logged in to view maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{},
        'is_owner':'bool',
        'cmp':{},
        'characters':{}
    }}}}
})
async def get_map(fingerprint: str, campaign: str, map: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to view maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    chars = {}
    nc = [];
    for c in server.campaigns[campaign].characters:
        try:
            decache(c)
            chars[c] = server.characters[c].to_dict()
            nc.append(c)
        except ValueError:
            pass
    server.campaigns[campaign].characters = nc[:]
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map],
        'is_owner':campaign in server.connections[fingerprint].user.owned_campaigns,
        'cmp':server.campaigns[campaign].to_json(),
        'characters':chars
    }

@router.post('/modify/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def modify_map(fingerprint: str, campaign: str, map: str, model: MapModifyModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    if not campaign in server.connections[fingerprint].user.owned_campaigns:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You are not the owner of this campaign.'}
    cd = 'server.campaigns[campaign].maps[map]["'+'"]["'.join(model.path.split('.'))+'"]'
    try:
        prev = eval(cd,globals(),locals())
        exec(cd+'=model.value',globals(),locals())
    except KeyError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':f'Setting not found for "{model.path}".'}
    server.campaigns[campaign].update()
    logger.info('User {user} changed setting {path} from "{previous}" to "{current}" on map {map} in campaign {cmp}'.format(
        user=fingerprint,
        path=model.path,
        previous=prev,
        current=eval(cd,globals(),locals()),
        map=map,
        cmp=campaign
    ))
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

@router.post('/modify_batch/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def modify_map_batch(fingerprint: str, campaign: str, map: str, model: BatchModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    if not campaign in server.connections[fingerprint].user.owned_campaigns:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You are not the owner of this campaign.'}
    
    for item in model.batch:
        path = item['path']
        val = item['value']
        cd = 'server.campaigns[campaign].maps[map]["'+'"]["'.join(path.split('.'))+'"]'
        try:
            prev = eval(cd,globals(),locals())
            exec(cd+'=val',globals(),locals())
        except KeyError:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {'result':f'Setting not found for "{path}".'}
    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

@router.post('/entity/add/obscure/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def add_obscure(fingerprint: str, campaign: str, map: str, model: ObscureModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    if not campaign in server.connections[fingerprint].user.owned_campaigns:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You are not the owner of this campaign.'}
    server.campaigns[campaign].maps[map]['entities'][secrets.token_urlsafe(32)] = {
        'obscure':True,
        'pos':{
            'x':model.x,
            'y':model.y
        },
        'dim':{
            'w':model.w,
            'h':model.h
        }
    }
    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

@router.post('/entity/remove/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def remove_entity(fingerprint: str, campaign: str, map: str, model: EntityReferenceModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    if not campaign in server.connections[fingerprint].user.owned_campaigns:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You are not the owner of this campaign.'}
    if model.eid in server.campaigns[campaign].maps[map]['entities'].keys():
        del server.campaigns[campaign].maps[map]['entities'][model.eid]
    
    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

@router.post('/creatures/search/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def search_creatures(fingerprint: str, campaign: str, map: str, model: SearchCreaturesModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    
    creatures = []
    for k in server.campaigns[campaign].homebrew.keys():
        for c in server.campaigns[campaign].homebrew[k]['creatures']:
            if c.name.lower() in model.search.lower() or model.search.lower() in c.name.lower():
                creatures.append(c)
    creatures.extend(get_creatures(limit=model.limit,search=model.search))

    return {
        'result':'Success.',
        'creatures':creatures
    }

@router.post('/entity/add/player/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def add_player(fingerprint: str, campaign: str, map: str, model: AddCharacterToMapModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    if not model.charid in server.campaigns[campaign].characters:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':f'Character {model.charid} not in campaign.'}
    server.campaigns[campaign].maps[map]['entities'][secrets.token_urlsafe(32)] = {
        'character':True,
        'pos':{
            'x':model.x,
            'y':model.y
        },
        'id':model.charid
    }
    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

@router.post('/entity/modify/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def modify_entity(fingerprint: str, campaign: str, map: str, model: ModifyEntityModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    try:
        item = eval(f'server.campaigns[campaign].maps[map]["entities"]["{model.entity}"]',globals(),locals())
    except IndexError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':f'Map {model.entity} not found.'}
    if 'character' in item.keys():
        if item['character']:
            if item['id'] in server.connections[fingerprint].user.owned_characters or campaign in server.connections[fingerprint].user.owned_campaigns:
                pass
            else:
                response.status_code = status.HTTP_403_FORBIDDEN
                server.campaigns[campaign].update()
                return {'result':'You are not the owner of this character.'}
        else:
            response.status_code = status.HTTP_403_FORBIDDEN
            server.campaigns[campaign].update()
            return {'result':'You are not the owner of this campaign.'}
    else:
        if not campaign in server.connections[fingerprint].user.owned_campaigns:
            response.status_code = status.HTTP_403_FORBIDDEN
            server.campaigns[campaign].update()
            return {'result':'You are not the owner of this campaign.'}

    for item in model.batch:
        path = item['path']
        val = item['value']
        cd = f'server.campaigns[campaign].maps[map]["entities"]["{model.entity}"]["'+'"]["'.join(path.split('.'))+'"]'
        try:
            prev = eval(cd,globals(),locals())
            exec(cd+'=val',globals(),locals())
        except KeyError:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {'result':f'Setting not found for "{path}".'}
    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

@router.post('/entity/add/npc/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def add_npc(fingerprint: str, campaign: str, map: str, model: NPCModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    if not campaign in server.connections[fingerprint].user.owned_campaigns:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You are not the owner of this campaign.'}
    server.campaigns[campaign].maps[map]['entities'][secrets.token_urlsafe(32)] = {
        'npc':True,
        'pos':{
            'x':model.x,
            'y':model.y
        },
        'data':model.data,
        'displaying_statblock':False
    }
    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

@router.post('/chat/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def post_chat(fingerprint: str, campaign: str, map: str, model: PostChatModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    if len(model.value) <= int(CONFIG['CAMPAIGNS']['max_chat_length']):
        val = model.value
        server.campaigns[campaign].maps[map]['chat'].append({
            'content':val,
            'author':server.connections[fingerprint].user.settings['display_name'],
            'time':time.strftime('%x %I:%M %p'),
            'uid':server.connections[fingerprint].user.uid,
            'iid':secrets.token_urlsafe(16)
        })
    else:
        val = model.value[:int(CONFIG['CAMPAIGNS']['max_chat_length'])]
        server.campaigns[campaign].maps[map]['chat'].append({
            'content':val,
            'author':server.connections[fingerprint].user.settings['display_name'],
            'time':time.strftime('%x %I:%M %p'),
            'uid':server.connections[fingerprint].user.uid,
            'iid':secrets.token_urlsafe(16)
        })
    if val.startswith('!') and len(val) > 1:
        ret = chatbot_interpret(val[1:],fingerprint,campaign,map)
        if ret:
            server.campaigns[campaign].maps[map]['chat'].append({
                'content':ret,
                'author':'System',
                'time':time.strftime('%x %I:%M %p'),
                'uid':'',
                'iid':secrets.token_urlsafe(16)
            })
    
    if len(server.campaigns[campaign].maps[map]['chat']) > int(CONFIG['CAMPAIGNS']['max_chat_items']):
        del server.campaigns[campaign].maps[map]['chat'][0]

    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

@router.post('/chat/delete/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def delete_chat(fingerprint: str, campaign: str, map: str, model: DeleteChatModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    
    found = -1
    c = 0
    for i in server.campaigns[campaign].maps[map]['chat']:
        if i['iid'] == model.iid:
            found = c
            break
        c += 1
    if (found >= 0):
        if campaign in server.connections[fingerprint].user.owned_campaigns or server.campaigns[campaign].maps[map]['chat'][found]['uid'] == server.connections[fingerprint].user.uid:
            del server.campaigns[campaign].maps[map]['chat'][found]
        else:
            response.status_code = status.HTTP_403_FORBIDDEN
            server.campaigns[campaign].update()
            return {'result':'You are not the owner of this campaign, and have not authored this chat message.'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':f'Message {model.iid} not found.'}

    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }

