from fastapi import APIRouter, status, Request, Response
from util import *
from classes import *
from _runtime import server, CONFIG
import logging, random, hashlib
from pydantic import BaseModel
from models import *
logger = logging.getLogger("uvicorn.error")

router = APIRouter()

@router.get('/connection/status/{fingerprint}/',responses={
    404: {'model':SimpleResult,'description':'Connection ID not found.'},
    200: {
        'description': 'Return basic busy-waiting information.',
        'content': {
            'application/json': {
                'example':{
                    'result':'Fetched data.',
                    'endpoints':{
                        'client':True,
                        'connection':True,
                        'characters':True,
                        'campaigns':True
                    },
                    'loggedIn':True,
                    'userId':None
                }
            }
        },
        'model':StatusResponseModel
    }
}) # Get connection status
async def connection_status(fingerprint: str, response: Response):
    if fingerprint in server.connections.keys():
        server.connections[fingerprint].timeout = time.time()+5
        return {
            'result':'Fetched data.',
            'endpoints':{
                'client':server.connections[fingerprint].user.check() or server.check('client'),
                'connection':server.connections[fingerprint].check(),
                'characters':any([i.check() for i in server.characters.values()]) or server.connections[fingerprint].char_update.check() or server.check('characters'),
                'campaigns':any([i.check() for i in server.campaigns.values()]) or server.connections[fingerprint].camp_update.check() or server.check('campaigns')
            },
            'loggedIn':server.connections[fingerprint].logged_in,
            'userId':server.connections[fingerprint].uid
        }
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection ID not in system. Create a connection.'}

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

@router.post('/login/',responses={
    404: {'model':SimpleResult,'description':'Connection or User not found','content':{'application/json':{'example':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'Incorrect email or password','content':{'application/json':{'example':{'result':'Incorrect email or password.'}}}},
    200: {'model':SimpleResult,'description':'Successful. Client logs in to existing account.','content':{'application/json':{'example':{'result':'Success.'}}}}
}) # Logs into server
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
@router.post('/login/new/',responses={
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example.':{'result':'Connection not found for user.'}}}},
    403: {'model':SimpleResult,'description':'User with email already exists, password is incorrect.','content':{'application/json':{'example':{'result':'User already exists, password is incorrect.'}}}},
    200: {'model':SimpleResult,'description':'Successful. Client logs in to account.','content':{'application/json':{'example':{'result':'Success.'}}}}
}) # Adds new account, or logs in if one already exists
async def new_user(model: SignUpModel, response: Response):
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
        logger.info('New user: '+model.username+' - '+model.name)
        uid = hashlib.sha256(str(random.random()).encode('utf-8')).hexdigest()
        server.users[uid] = User(uid,model.username,model.hashword,model.name)
        server.users[uid].connection = model.fingerprint
        server.connections[model.fingerprint].user = server.users[uid]
        server.connections[model.fingerprint].logged_in = True
        server.connections[model.fingerprint].uid = uid
        server.users[uid].update()
        return {'result':'Success.','uid':uid}
@router.post('/login/exit/',responses={
    404: {'model':SimpleResult,'description':'Connection not found','content':{'application/json':{'example.':{'result':'Connection not found for user.'}}}},
    405: {'model':SimpleResult,'description':'Cannot log out, as the user is not logged in.','content':{'application/json':{'example':{'result':'User is not logged in.'}}}},
    200: {'model':SimpleResult,'description':'Successful. Client signs out of account.','content':{'application/json':{'example':{'result':'Success.'}}}}
}) # Logs out
async def logout(model: ConnectionModel, response: Response):
    if not model.fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    
    if server.connections[model.fingerprint].logged_in:
        cache_user(server.connections[model.fingerprint].uid)
        server.connections[model.fingerprint].user.connection = None
        server.connections[model.fingerprint].user = User('','','','',cache=False)
        server.connections[model.fingerprint].logged_in = False
        server.connections[model.fingerprint].uid = None
        logger.info('User '+model.fingerprint+' logged out.');
        return {'result':'Success.'}
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'User is not logged in.'}

@router.get('/config/{section}/{variable}/',responses={
    404: {'model':SimpleResult,'description':'Section or Variable','content':{'application/json':{'example.':{'result':'Connection not found for user.'}}}},
    200: {'model':SimpleResult,'description':'Successful. Returns value of server config.','content':{'application/json':{'example':{
        'result':'Success.',
        'section':'string',
        'variable':'string',
        'value':'string'
    }}}}
})
async def server_config(section: str, variable: str, response: Response):
    try:
        return {
            'result': 'Success',
            'section': section,
            'variable': variable,
            'value':CONFIG[section][variable]
        }
    except:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Section or Variable not found.'}

@router.post('/config/batch/',responses={
    404: {'model':SimpleResult,'description':'Section or Variable not found','content':{'application/json':{'example.':{'result':'Section or Variable not found.'}}}},
    200: {'model':SimpleResult,'description':'Successful. Returns dictionary of values.','content':{'application/json':{'example':{
        'result':'Success.',
        'values':{
            'SECTION':{
                'var1':'value',
                'var2':'value',
                'etc':'etc'
            },
            'SECTION2':{
                'var1':'value',
                'var2':'value',
                'etc':'etc'
            }
        }
    }}}}
})
async def server_config_batch(model: BatchConfigModel, response: Response):
    vals = {}
    for s in model.batch.keys():
        vals[s] = {}
        for v in model.batch[s]:
            try:
                vals[s][v] = CONFIG[s][v]
            except:
                response.status_code = status.HTTP_404_NOT_FOUND
                return {'result':f'Section {s} or Variable {v} not found.'}
    return {
        'result':'Success.',
        'values':vals
    }

        