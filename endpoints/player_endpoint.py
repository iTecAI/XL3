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
        'data':{}
    }}}}
})
async def get_map(fingerprint: str, campaign: str, map: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    if not check_access(fingerprint,campaign,map):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Map or Campaign not found, or you don\'t have access to it.'}
    return {
        'result':'Success.',
        'data':server.campaigns[campaign].maps[map]
    }