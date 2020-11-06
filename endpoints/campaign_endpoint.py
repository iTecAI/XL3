from endpoints.character_endpoint import decache
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
    for i in reg.keys():
        if i in server.connections[fp].user.owned_campaigns or i in server.connections[fp].user.participating_campaigns:
            with open(os.path.join('database','campaigns',i+'.pkl'),'rb') as f:
                server.campaigns[i] = pickle.load(f)
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
                'maps':'dict of maps',
                'homebrew':'list of homebrew creatures'
            }
        ],
        'new_campaign':{
                'id':'id',
                'owner':'owner ID',
                'name':'name',
                'characters':'character ids',
                'settings':'settings dict',
                'maps':'dict of maps',
                'homebrew':'list of homebrew creatures'
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

@router.post('/join/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':SimpleResult,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.'
    }}}}
})
async def join_campaign(fingerprint: str, model: JoinCampaignModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    
    if model.campaign in server.campaigns.keys():
        if server.campaigns[model.campaign].password_protected:
            if server.campaigns[model.campaign].passhash == model.passhash:
                pass
            else:
                response.status_code = status.HTTP_403_FORBIDDEN
                return {'result':'Incorrect password.'}
        else:
            pass
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign not found.'}
    if not model.campaign in server.connections[fingerprint].user.participating_campaigns:
        server.connections[fingerprint].user.participating_campaigns.append(model.campaign)
    server.connections[fingerprint].user.update()
    server.campaigns[model.campaign].update()
    return {'result':'Success.'}

@router.post('/check_password_protected/{campaign}/',responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view characters.'}}}},
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':SimpleResult,'description':'Returns campaign data.','content':{'application/json':{'example':{
        'result':'Success.',
        'password_protected':'bool'
    }}}}
})
async def passcheck_campaign(fingerprint: str, campaign: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to create campaigns.'}
    
    if campaign in server.campaigns.keys():
        return {'result':'Success.','password_protected':server.campaigns[campaign].password_protected}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign not found.'}

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

@router.post('/batch/', responses={
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
    200: {'model':SimpleResult,'description':'Deletes campaign, returns success.','content':{'application/json':{'example':{
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
        for i in server.campaigns[campaign].maps.keys():
            try:
                del_image(server.campaigns[campaign].maps[i]['image_id'])
            except KeyError:
                pass
        del server.campaigns[campaign]
        for u in list(server.users.keys()):
            if campaign in server.users[u].owned_campaigns:
                server.users[u].owned_campaigns.remove(campaign)
            if campaign in server.users[u].participating_campaigns:
                server.users[u].participating_campaigns.remove(campaign)
            server.users[u].update()
        with open(os.path.join('database','campaigns','registry.json'),'r') as f:
            reg = json.load(f)
        with open(os.path.join('database','campaigns','registry.json'),'w') as f:
            if campaign in reg.keys():
                del reg[campaign]
                f.write(json.dumps(reg))
        if os.path.exists(os.path.join('database','campaigns',campaign+'.pkl')):
            os.remove(os.path.join('database','campaigns',campaign+'.pkl'))
        for c in list(server.campaigns.keys()):
            server.campaigns[c].update()
        server.updates['campaigns'] = True
        server.connections[fingerprint].user.update()
        return {'result':'Success'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign not found or you do not have ownership of it.'}

@router.post('/{campaign}/add_character/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view campaigns.'}}}},
    404: {'model':SimpleResult,'description':'Connection or Campaign not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':SimpleResult,'description':'Adds character, returns success.','content':{'application/json':{'example':{
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
    if check_access(fingerprint,campaign) and model.charid in server.characters.keys():
        if len(server.campaigns[campaign].characters) >= int(CONFIG['CAMPAIGNS']['characters_per_campaign']):
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {'result':f'Exceeded maximum number of characters for campaign. Max: {CONFIG["CAMPAIGNS"]["characters_per_campaign"]}'}
        logger.info(f'User {fingerprint} is adding a character with ID {model.charid} to campaign with ID {campaign}.')
        if not model.charid in server.campaigns[campaign].characters:
            decache(model.charid)
            server.campaigns[campaign].characters.append(model.charid)
            server.connections[fingerprint].user.update()
            server.campaigns[campaign].update()
            server.characters[model.charid].campaign = campaign
            server.characters[model.charid].update()
            server.characters[model.charid].cache()
        return {'result':'Success'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign/Character not found or you do not have access to it.'}

@router.post('/{campaign}/remove_character/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view campaigns.'}}}},
    404: {'model':SimpleResult,'description':'Connection or Campaign not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    200: {'model':SimpleResult,'description':'Removes character, returns success.','content':{'application/json':{'example':{
        'result':'Success.'
    }}}}
})
async def remove_character_from_campaign(fingerprint: str, campaign: str, model: AddCharacterToCmpModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to manage characters.'}
    if check_access(fingerprint,campaign):
        if model.charid in server.campaigns[campaign].characters:
            decache(model.charid)
            server.campaigns[campaign].characters.remove(model.charid)
            server.connections[fingerprint].user.update()
            server.campaigns[campaign].update()
            server.characters[model.charid].campaign = ''
            server.characters[model.charid].update()
            server.characters[model.charid].cache()
            logger.info(f'User {fingerprint} is removing a character with ID {model.charid} from campaign with ID {campaign}.')
            return {'result':'Success'}
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {'result':'Character not found or it is not present in this campaign.'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Campaign not found or you do not have access to it.'}

@router.post('/{campaign}/setting/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view campaigns.'}}}},
    404: {'model':SimpleResult,'description':'Connection, Campaign, or Setting not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'Not allowed to modify campaign.','content':{'application/json':{'example':{'result':'You do not own this campaign.'}}}},
    200: {'model':SimpleResult,'description':'Changes setting, returns success.','content':{'application/json':{'example':{
        'result':'Success.'
    }}}}
})
async def modify_campaign_settings(fingerprint: str, campaign: str, model: CampaignSettingChangeModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to manage campaigns.'}
    if check_access(fingerprint,campaign) and campaign in server.connections[fingerprint].user.owned_campaigns:
        try:
            if model.name in server.campaigns[campaign].settings.keys():
                if (
                    type(model.value) == int and server.campaigns[campaign].settings[model.name]['type'] == 'int'
                    and server.campaigns[campaign].settings[model.name]['value'] >= server.campaigns[campaign].settings[model.name]['min']
                    and server.campaigns[campaign].settings[model.name]['value'] <= server.campaigns[campaign].settings[model.name]['max']
                ):
                    server.campaigns[campaign].settings[model.name]['value'] = model.value
                elif type(model.value) == bool and server.campaigns[campaign].settings[model.name]['type'] == 'bool':
                    server.campaigns[campaign].settings[model.name]['value'] = model.value
                elif type(model.value) == str and server.campaigns[campaign].settings[model.name]['type'] == 'str':
                    server.campaigns[campaign].settings[model.name]['value'] = model.value
                else:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    return {'result':
                        'Bad value. Given setting: {setting}. Given value: [{value}] of type {vtype}. Setting parameters: {sparams}'.format(
                            setting=model.name,
                            value=model.value,
                            vtype=str(type(model.value)),
                            sparams=json.dumps(server.campaigns[campaign].settings[model.name])
                        )
                    }
                logger.info('User {fp} changed setting "{setting}" to "{value}" (type {vtype}) in campaign {cmp}.'.format(
                    setting=model.name,
                    value=model.value,
                    vtype=str(type(model.value)),
                    fp=fingerprint,
                    cmp=campaign
                ))
                if model.name in ['variant_encumbrance','coin_weight','roll_hp']:
                    for c in server.campaigns[campaign].characters:
                        server.characters[c].options[model.name] = model.value
                        server.characters[c].cache()
                        server.characters[c].update()
        except Exception as e:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {'result':
                'Bad value, caused exception [{exc}]. Given setting: {setting}. Given value: [{value}] of type {vtype}. Setting parameters: {sparams}'.format(
                    exc=str(e),
                    setting=model.name,
                    value=model.value,
                    vtype=str(type(model.value)),
                    sparams=json.dumps(server.campaigns[campaign].settings[model.name])
                )
            }
        server.campaigns[campaign].update()
    else:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this campaign.'}

@router.post('/{campaign}/maps/add/', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view campaigns.'}}}},
    404: {'model':SimpleResult,'description':'Connection, Campaign, or Setting not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'Not allowed to modify campaign.','content':{'application/json':{'example':{'result':'You do not own this campaign.'}}}},
    200: {'model':SimpleResult,'description':'Adds map, returns success.','content':{'application/json':{'example':{
        'result':'Success.'
    }}}}
})
async def add_map_to_campaign(fingerprint: str, campaign: str, model: AddMapToCmpModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to manage campaigns.'}
    if check_access(fingerprint,campaign) and campaign in server.connections[fingerprint].user.owned_campaigns:
        if len(server.campaigns[campaign].maps.keys()) >= int(CONFIG['CAMPAIGNS']['maps_per_campaign']):
            response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
            return {'result':f"You have reached the maximum number of maps: {CONFIG['CAMPAIGNS']['maps_per_campaign']}"}
        try:
            iid = add_image(model.data)
        except ValueError:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {'result':'You must use a .png or .jpeg image.'}
        except Exception as e:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {'result':'Malformed data URI, please check image. Error: '+str(e)}
        server.campaigns[campaign].maps[iid] = {
            'image_id':iid,
            'obscuration':{},
            'entities':{},
            'grid':{
                'columns':model.columns,
                'rows':model.rows,
                'size':model.gridsize
            },
            'name':model.name
        }
        server.campaigns[campaign].update()
        return {'result':'Success.'}
    else:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this campaign.'}

@router.post('/{campaign}/maps/remove/{map}', responses={
    405: {'model':SimpleResult,'description':'You must be logged in to create campaigns.','content':{'application/json':{'example':{'result':'You must be logged in to view campaigns.'}}}},
    404: {'model':SimpleResult,'description':'Connection, Campaign, or Setting not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'Not allowed to modify campaign.','content':{'application/json':{'example':{'result':'You do not own this campaign.'}}}},
    200: {'model':SimpleResult,'description':'Adds map, returns success.','content':{'application/json':{'example':{
        'result':'Success.'
    }}}}
})
async def remove_map_from_campaign(fingerprint: str, campaign: str, map: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    if not server.connections[fingerprint].logged_in:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to manage campaigns.'}
    if check_access(fingerprint,campaign) and campaign in server.connections[fingerprint].user.owned_campaigns:
        if map in server.campaigns[campaign].maps.keys():
            try:
                del server.campaigns[campaign].maps[map]
                del_image(map)
            except KeyError:
                pass
            server.campaigns[campaign].update()
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {'result':'Map not found.'}
    else:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {'result':'You do not own this campaign.'}