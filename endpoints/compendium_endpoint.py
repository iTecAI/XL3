from fastapi import APIRouter, status, Request, Response
from util import *
from classes import *
from _runtime import server
import logging, random, hashlib
from pydantic import BaseModel
from models import *
from _api import *
logger = logging.getLogger("uvicorn.error")

router = APIRouter()

@router.get('/section/{name}/',responses={
    200: {'model':CompSectionResponseModel,'description':'Section is returned in HTML form.','content':{'application/json':{'example':{'result':'Success.','content':'<html>'}}}},
    404: {'model':SimpleResult,'description':'Section not found.','content':{'application/json':{'example':{'result':'Section not found.'}}}}
})
async def get_comp_section(name: str, response: Response):
    try:
        return {'result':'Success.','content':get_section(name)}
    except ValueError:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Section not found.'}

@router.get('/search/{endpoint}/',responses={
    200: {'model':CompSectionResponseModel,'description':'List of results is returned.','content':{'application/json':{'example':{'result':'Success.','search_results':[]}}}},
    404: {'model':SimpleResult,'description':'Endpoint not found.','content':{'application/json':{'example':{'result':'Endpoint not found.'}}}}
})
async def search_comp(endpoint: str, response: Response, search: str = ''):
    if search == '#':
        return get5e(endpoint,limit=1500)
    else:
        return get5e(endpoint,search=search,limit=1500)

