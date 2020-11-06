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
    for c in server.campaigns[campaign].characters:
        decache(c)
        chars[c] = server.characters[c].to_dict()
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
    server.campaigns[campaign].maps[map]['entities'][secrets.token_urlsafe(32)] = {
        'type':'obscure',
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

@router.post('/entity/remove/obscure/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to modify maps.','content':{'application/json':{'example':{'result':'You must be logged in to modify maps.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MapDataResponseModel,'description':'Returns map data.','content':{'application/json':{'example':{
        'result':'Success.',
        'data':{}
    }}}}
})
async def remove_obscure(fingerprint: str, campaign: str, map: str, model: EntityReferenceModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to modify maps.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    #if model.eid in server.campaigns[campaign].maps[map]['entities'].keys():
    del server.campaigns[campaign].maps[map]['entities'][model.eid]
    
    server.campaigns[campaign].update()
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }


