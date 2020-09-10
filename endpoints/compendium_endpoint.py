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

