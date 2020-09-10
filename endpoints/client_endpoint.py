from fastapi import APIRouter, status, Request, Response
from util import *
from classes import *
from _runtime import server
import logging, random, hashlib
from pydantic import BaseModel
from models import *
logger = logging.getLogger("uvicorn.error")

router = APIRouter()

@router.post('/settings/set/{setting}/',responses={
    404: {'model':SimpleResult,'description':'Connection or Setting not found','content':{'application/json':{'example.':{'result':'You must be logged in to do that.'}}}},
    405: {'model':SimpleResult,'description':'Cannot edit client settings, as the user is not logged in.','content':{'application/json':{'example':{'result':'User is not logged in.'}}}},
    200: {'model':SimpleResult,'description':'Successful. Setting is changed','content':{'application/json':{'example':{'result':'Success.'}}}}
})
async def edit_client_settings(fingerprint: str, setting: str, model: ClientSettingsModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found.'}
    
    if server.connections[fingerprint].logged_in:
        if setting in server.connections[fingerprint].user.settings.keys():
            server.connections[fingerprint].user.settings[setting] = model.value
            logger.info('User '+server.connections[fingerprint].user.username+' changed a setting: '+setting+' = '+model.value)
            server.connections[fingerprint].user.update()
            return {'result':'Success'}
        elif setting == 'email':
            server.connections[fingerprint].user.username = model.value
            logger.info('User '+server.connections[fingerprint].user.username+' changed a setting: '+setting+' = '+model.value)
            server.connections[fingerprint].user.update()
            return {'result':'Success'}
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {'result':'Setting '+setting+' not found.'}
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to do that.'}

@router.get('/settings/{setting}/',responses={
    404: {'model':SimpleResult,'description':'Connection or Setting not found','content':{'application/json':{'example.':{'result':'You must be logged in to do that.'}}}},
    405: {'model':SimpleResult,'description':'Cannot get client settings, as the user is not logged in.','content':{'application/json':{'example':{'result':'User is not logged in.'}}}},
    200: {'model':SettingResponseModel,'description':'Successful. Returns setting value.','content':{'application/json':{'example':{'result':'Success.','setting':'Setting Name','value':'Setting Value'}}}}
})
async def get_specific_client_setting(fingerprint: str, setting: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found.'}
    
    if server.connections[fingerprint].logged_in:
        if setting in server.connections[fingerprint].user.settings.keys():
            return {'result':'Success','setting':setting,'value':server.connections[fingerprint].user.settings[setting]}
        elif setting == 'email':
            return {'result':'Success','setting':setting,'value':server.connections[fingerprint].user.email}
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {'result':'Setting '+setting+' not found.'}
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to do that.'}

@router.get('/settings/',responses={
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example.':{'result':'You must be logged in to do that.'}}}},
    405: {'model':SimpleResult,'description':'Cannot get client settings, as the user is not logged in.','content':{'application/json':{'example':{'result':'User is not logged in.'}}}},
    200: {'model':AllSettingsResponseModel,'description':'Successful. Returns setting value.','content':{'application/json':{'example':{'result':'Success.','settings':{'Setting Name':'Setting Value','Foo':'Bar'}}}}}
})
async def get_client_settings(fingerprint: str, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found.'}
    
    if server.connections[fingerprint].logged_in:
        _settings = server.connections[fingerprint].user.settings.copy()
        _settings['email'] = server.connections[fingerprint].user.username
        return {'result':'Success','settings':_settings}
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to do that.'}

@router.post('/password/check/',responses={
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example.':{'result':'You must be logged in to do that.'}}}},
    405: {'model':SimpleResult,'description':'Cannot check password, as the user is not logged in.','content':{'application/json':{'example':{'result':'User is not logged in.'}}}},
    200: {'model':PasswordCheckResponseModel,'description':'Successful. Returns whether the password matches.','content':{'application/json':{'example':{'result':'Success.','match':True}}}}
})
async def check_password(fingerprint: str, model: PasswordCheckModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found.'}
    
    if server.connections[fingerprint].logged_in:
        if server.connections[fingerprint].user.password_hash == model.hashword:
            return {'result':'Success','match':True}
        else:
            return {'result':'Success','match':False}
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to do that.'}

@router.post('/password/change/',responses={
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example.':{'result':'You must be logged in to do that.'}}}},
    405: {'model':SimpleResult,'description':'Cannot change password, as the user is not logged in.','content':{'application/json':{'example':{'result':'User is not logged in.'}}}},
    403: {'model':SimpleResult,'description':'Cannot change password, as the previous password provided was incorrect.','content':{'application/json':{'example':{'result':'Previous password incorrect.'}}}},
    200: {'model':SimpleResult,'description':'Successful. Returns whether the password matches.','content':{'application/json':{'example':{'result':'Success.'}}}}
})
async def change_password(fingerprint: str, model: PasswordChangeModel, response: Response):
    if not fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found.'}
    
    if server.connections[fingerprint].logged_in:
        if server.connections[fingerprint].user.password_hash == model.hashword:
            server.connections[fingerprint].user.password_hash = model.new_hashword
            return {'result':'Success.'}
        else:
            response.status_code = status.HTTP_403_FORBIDDEN
            return {'result':'Previous password incorrect.'}
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'You must be logged in to do that.'}