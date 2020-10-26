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

router = APIRouter()

def check_access(fp,cid):
    pass

@router.post('/new/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MultipleCharacterResponseModel,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.',
        'campaigns':[]
    }}}}
})
async def new_campaign(fingerprint: str, model: NewCampaignModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    
    if len(server.connections[fingerprint].user.owned_campaigns) < int(CONFIG['CAMPAIGNS']['cmax_campaigns']):
        logger.info(f'User {fingerprint} is creating a new campaign.')
        ncp = Campaign(server.connections[fingerprint].users.uid, model.name)
        server.connections[fingerprint].user.owned_campaigns.append(ncp.id)
        server.connections[fingerprint].user.participating_campaigns.append(ncp.id)
        server.campaigns[ncp.id] = ncp
        return {
            'result':'Success.',
            'campaigns':server.connections[fingerprint].user.owned_campaigns
        }
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You have reached the maximum amount of campaigns.'}

@router.get('/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MultipleCharacterResponseModel,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.',
        'campaigns':[]
    }}}}
})
async def get_campaigns(fingerprint: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    
    return {
        'result':'Success.',
        'owned_campaigns':server.connections[fingerprint].user.owned_campaigns,
        'participating_campaigns':server.connections[fingerprint].user.participating_campaigns
    }

@router.get('/{campaign}/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MultipleCharacterResponseModel,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.',
        'campaigns':[]
    }}}}
})
async def get_campaign(fingerprint: str, campaign: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    
    if (campaign in server.connections[fingerprint].user.owned_campaigns or campaign in server.connections[fingerprint].user.participating_campaigns) and campaign in server.campaigns.keys():
        return {
            'result':'Success.',
            'campaign':server.campaigns[campaign].to_json()
        }
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign not found.'}
