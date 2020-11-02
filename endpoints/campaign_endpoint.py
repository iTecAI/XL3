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
    with open(os.path.join('database','campaigns','registry.json'),'r') as f:
        reg = json.load(f)
    if cid in reg.keys() and cid in server.campaigns.keys():
        with open(os.path.join('database','campaigns',cid+'.pkl'),'rb') as f:
            server.campaigns[cid] = pickle.load(f)
        return cid in server.connections[fp].user.owned_campaigns or cid in server.connections[fp].user.participating_campaigns
    else:
        return False

@router.post('/new/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':NewCampaignModel,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.',
        'owned_campaigns':[
            {
                'id':'id',
                'owner':'owner ID',
                'name':'name',
                'characters':'character ids',
                'settings':'settings dict',
                'maps':'dict of maps'
            }
        ],
        'new_campaign':{
                'id':'id',
                'owner':'owner ID',
                'name':'name',
                'characters':'character ids',
                'settings':'settings dict',
                'maps':'dict of maps'
            }
    }}}}
})
async def new_campaign(fingerprint: str, model: NewCampaignModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    
    if len(server.connections[fingerprint].user.owned_campaigns) < int(CONFIG['CAMPAIGNS']['max_campaigns']):
        logger.info(f'User {fingerprint} is creating a new campaign.')
        ncp = Campaign(server.connections[fingerprint].user.uid, model.name, model.password)
        server.connections[fingerprint].user.owned_campaigns.append(ncp.id)
        server.connections[fingerprint].user.participating_campaigns.append(ncp.id)
        server.campaigns[ncp.id] = ncp
        rd = {
            'result':'Success.',
            'owned_campaigns':[server.campaigns[i].to_json() for i in server.campaigns.keys() if server.campaigns[i].id in server.connections[fingerprint].user.owned_campaigns],
            'new_campaign':ncp.to_json()
        }
        server.connections[fingerprint].user.update()
        return rd
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You have reached the maximum amount of campaigns.'}

@router.get('/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MultipleCampaignResponseModel,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.',
        'owned_campaigns':[],
        'participating_campaigns':[]
    }}}}
})
async def get_campaigns(fingerprint: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    with open(os.path.join('database','campaigns','registry.json'),'r') as f:
        reg = json.load(f)
    for i in reg.keys():
        if i in server.connections[fingerprint].user.owned_campaigns or i in server.connections[fingerprint].user.participating_campaigns:
            with open(os.path.join('database','campaigns',i+'.pkl'),'rb') as f:
                server.campaigns[i] = pickle.load(f)
    
    return {
        'result':'Success.',
        'owned_campaigns':[server.campaigns[i].to_json() for i in server.campaigns.keys() if server.campaigns[i].id in server.connections[fingerprint].user.owned_campaigns],
        'participating_campaigns':[server.campaigns[i].to_json() for i in server.campaigns.keys() if server.campaigns[i].id in server.connections[fingerprint].user.participating_campaigns]
    }

@router.get('/batch/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':MultipleCampaignResponseModel,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.',
        'owned_campaigns':[],
        'participating_campaigns':[]
    }}}}
})
async def get_campaigns_batch(fingerprint: str, model: BatchModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    with open(os.path.join('database','campaigns','registry.json'),'r') as f:
        reg = json.load(f)
    for i in reg.keys():
        if i in server.connections[fingerprint].user.owned_campaigns or i in server.connections[fingerprint].user.participating_campaigns:
            with open(os.path.join('database','campaigns',i+'.pkl'),'rb') as f:
                server.campaigns[i] = pickle.load(f)
    
    return {
        'result':'Success.',
        'owned_campaigns':[server.campaigns[i].to_json() for i in server.campaigns.keys() if server.campaigns[i].id in server.connections[fingerprint].user.owned_campaigns and server.campaigns[i].id in model.batch],
        'participating_campaigns':[server.campaigns[i].to_json() for i in server.campaigns.keys() if server.campaigns[i].id in server.connections[fingerprint].user.participating_campaigns and server.campaigns[i].id in model.batch]
    }

@router.get('/{campaign}/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':CampaignResponseModel,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.',
        'campaign':{}
    }}}}
})
async def get_campaign(fingerprint: str, campaign: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    if check_access(fingerprint,campaign):
        return {
            'result':'Success.',
            'campaign':server.campaigns[campaign].to_json()
        }
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign not found.'}

@router.post('/{campaign}/delete/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view campaigns.'}}}},
    404: {'model':SimpleResult,'description':'Connection or Campaign not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':SimpleResult,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.'
    }}}}
})
async def delete_campaign(fingerprint: str, campaign: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to delete campaigns.'}
    if check_access(fingerprint,campaign) and campaign in server.connections[fingerprint].user.owned_campaigns:
        logger.info(f'User {fingerprint} is deleting campaign with ID {campaign}.')
        del server.campaigns[campaign]
        for u in list(server.users.keys()):
            if campaign in server.users[u].owned_campaigns:
                server.users[u].owned_campaigns.remove(campaign)
            if campaign in server.users[u].participating_campaigns:
                server.users[u].participating_campaigns.remove(campaign)
            server.users[u].update()
        for c in list(server.campaigns.keys()):
            server.campaigns[c].update()
        server.connections[fingerprint].user.update()
        return {'result':'Success'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign not found or you do not have ownership of it.'}

@router.post('/{campaign}/add_character/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view campaigns.'}}}},
    404: {'model':SimpleResult,'description':'Connection or Campaign not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':SimpleResult,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.'
    }}}}
})
async def add_character_to_campaign(fingerprint: str, campaign: str, model: AddCharacterToCmpModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to manage characters.'}
    if check_access(fingerprint,campaign):
        if len(server.campaigns[campaign].characters) >= int(CONFIG['CAMPAIGNS']['characters_per_campaign']):
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {'result':f'Exceeded maximum number of characters for campaign. Max: {CONFIG["CAMPAIGNS"]["characters_per_campaign"]}'}
        logger.info(f'User {fingerprint} is adding a character with ID {model.charid} to campaign with ID {campaign}.')
        if not model.charid in server.campaigns[campaign].characters:
            server.campaigns[campaign].characters.append(model.charid)
            server.connections[fingerprint].user.update()
            server.campaigns[campaign].update()
        return {'result':'Success'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign not found or you do not have access to it.'}