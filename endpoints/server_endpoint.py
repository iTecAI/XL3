from fastapi import APIRouter, status, Request, Response
from util import *
from classes import *
from _runtime import server
import logging, random, hashlib
from pydantic import BaseModel
logger = logging.getLogger("uvicorn.error")

router = APIRouter()

@router.get('/connection/status/{fingerprint}/') # Get connection status
async def connection_status(fingerprint: str, response: Response):
    if fingerprint in server.connections.keys():
        server.connections[fingerprint].timeout = time.time()+5
        return {
            'result':'Fetched data.',
            'endpoints':{
                'client':server.connections[fingerprint].user.check(),
                'connection':server.connections[fingerprint].check()
            },
            'loggedIn':server.connections[fingerprint].logged_in
        }
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection ID not in system. Create a connection.'}

class ConnectionModel(BaseModel):
    fingerprint: str
@router.post('/connection/new/') # Make new connection
async def new_connection(model: ConnectionModel):
    if not model.fingerprint in server.connections.keys():
        logger.info('User '+model.fingerprint+' connected to server.')
        server.connections[model.fingerprint] = Connection()
        registry: dict = get_user_registry()
        for u in registry.keys():
            if registry[u]['connection'] == model.fingerprint:
                load_user(u)
                server.connections[model.fingerprint].user = server.users[u]
                server.connections[model.fingerprint].uid = u
                server.connections[model.fingerprint].logged_in = True
    return {}

class LoginModel(BaseModel):
    fingerprint: str
    username: str
    hashword: str
@router.post('/login/') # Logs into server
async def login(model: LoginModel, response: Response):
    if not model.fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    
    logger.info('User '+model.fingerprint+' logging in.')

    uid = None
    registry: dict = get_user_registry()
    for user in registry.keys():
        if registry[user]['username'] == model.username:
            uid = user
            break

    if uid != None:
        load_user(uid)
        if model.hashword == server.users[uid].password_hash:
            server.users[uid].connection = model.fingerprint
            server.connections[model.fingerprint].user = server.users[uid]
            server.connections[model.fingerprint].logged_in = True
            server.connections[model.fingerprint].uid = uid
            logger.info('Logged in: '+model.username)
            server.users[uid].update()
            return {'result':'Success.'}
        else:
            response.status_code = status.HTTP_403_FORBIDDEN
            return {'result':'Incorrect email or password.'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Email does not have an associated account.'}
@router.post('/login/new/') # Adds new account, or logs in if one already exists
async def new_user(model: LoginModel, response: Response):
    if not model.fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    logger.info('User '+model.fingerprint+' creating new acct.')

    uid = None
    registry = get_user_registry()
    for user in registry.keys():
        if registry[user]['username'] == model.username:
            uid = user
            break

    if uid != None:
        load_user(uid)
        if model.hashword == server.users[model.username].password_hash:
            server.users[uid].connection = model.fingerprint
            server.connections[model.fingerprint].user = server.users[uid]
            server.connections[model.fingerprint].logged_in = True
            server.connections[model.fingerprint].uid = uid
            logger.info('Logged in: '+model.username)
            server.users[uid].update()
            return {'result':'User exists, logged in.'}
        else:
            response.status_code = status.HTTP_403_FORBIDDEN
            return {'result':'User already exists, password is incorrect.'}
    else:
        logger.info('New user: '+model.username)
        uid = hashlib.sha256(str(random.random()).encode('utf-8')).hexdigest()
        server.users[uid] = User(uid,model.username,model.hashword)
        server.users[uid].connection = model.fingerprint
        server.connections[model.fingerprint].user = server.users[uid]
        server.connections[model.fingerprint].logged_in = True
        server.connections[model.fingerprint].uid = uid
        server.users[uid].update()
        return {'result':'Success.','uid':uid}
@router.post('/login/exit/') # Logs out
async def logout(model: ConnectionModel, response: Response):
    if not model.fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    
    if server.connections[model.fingerprint].logged_in:
        cache_user(server.connections[model.fingerprint].uid)
        server.connections[model.fingerprint].user.connection = None
        server.connections[model.fingerprint].user = User('','','',cache=False)
        server.connections[model.fingerprint].logged_in = False
        server.connections[model.fingerprint].uid = None
        logger.info('User '+model.fingerprint+' logged out.');
        return {'result':'Success.'}
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'User is not logged in.'}