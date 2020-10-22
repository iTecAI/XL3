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

router = APIRouter()

def check_access(fp,cid):
    pass

@router.get('/new/',responses={
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