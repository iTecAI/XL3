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

@router.get('/{iid}/')
async def get_image(iid: str, response: Response):
    with open(os.path.join('database','images','registry.json'),'r') as f:
        r = json.load(f)
    if iid in r.keys():
        return FileResponse(r[iid]['path'])
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':f'Image with IID {iid} does not exist.'}