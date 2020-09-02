from fastapi import FastAPI, Request, Body, Response, status
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi_utils.tasks import repeat_every
import uvicorn
import rsa
import os
import sys
import hashlib
from pydantic import BaseModel, create_model
from typing import Optional
from util import *
import urllib
import logging
import base64
import json
import random
import time

# Configs
VERSION = 0

logger = logging.getLogger("uvicorn.error")

'''if os.path.exists('prikey.pem') and os.path.exists('pubkey.pem'):
    try:
        logger.info('Loading RSA keys from PEM files.')
        with open('pubkey.pem','rb') as pub:
            PUBLIC_KEY = rsa.PublicKey.load_pkcs1(pub.read())
        with open('prikey.pem','rb') as pri:
            PRIVATE_KEY = rsa.PrivateKey.load_pkcs1(pri.read())
    except:
        logger.warning('Error loading old keys. Generating new ones.')
        PUBLIC_KEY, PRIVATE_KEY = rsa.newkeys(1024,accurate=True)
        with open('pubkey.pem','wb') as pub:
            pub.write(PUBLIC_KEY.save_pkcs1())
        with open('prikey.pem','wb') as pri:
            pri.write(PRIVATE_KEY.save_pkcs1())
else:
    logger.info('Generating new RSA keys.')
    PUBLIC_KEY, PRIVATE_KEY = rsa.newkeys(1024,accurate=True)
    with open('pubkey.pem','wb') as pub:
        pub.write(PUBLIC_KEY.save_pkcs1())
    with open('prikey.pem','wb') as pri:
        pri.write(PRIVATE_KEY.save_pkcs1())'''

# Setup
'''Build database'''
folders = ['users','sessions','campaigns']
for f in folders:
    try:
        os.makedirs(os.path.join('database',f))
    except FileExistsError:
        pass

'''Get OpenAPI configs'''
with open(os.path.join('config','openapi.json'),'r') as c:
    openapicfg = json.load(c)
    tags_meta =  openapicfg['metadata']

# Classes
class Server:
    def __init__(self,state=None):
        if state:
            pass
        else:
            self.connections: Connection = {}
            self.users: User = {}

class BaseItem:
    def __init__(self):
        self.updated = False
    def update(self):
        self.updated = True
    def check(self):
        temp = self.updated
        self.updated = False
        return temp
class Connection(BaseItem):
    def __init__(self):
        super().__init__()
        self.user: User = User('','','',cache=False)
        self.logged_in = False
        self.timeout = time.time()+5

class User(BaseItem):
    def __init__(self,uid,usn,pswhash,cache=True,connection=None):
        super().__init__()
        self.uid: str = uid
        self.username: str = usn
        self.password_hash: str = pswhash
        if cache:
            self.cachePath = os.path.join('database','users',self.uid+'.pkl')
        self.connection = connection

# App

server = Server() # Instantiate server instance - todo add stateful cache
app = FastAPI(openapi_tags=tags_meta)

# Server Endpoints

@app.get('/', response_class=HTMLResponse, include_in_schema=False) # Get index.html when navigated to root
async def root():
    with open(os.path.join('client','index.html'),'r') as f:
        return f.read()
    
@app.get('/server/connection/status/{fingerprint}/',tags=['server']) # Get connection status
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
@app.post('/server/connection/new/',tags=['server']) # Make new connection
async def new_connection(model: ConnectionModel):
    if not model.fingerprint in server.connections.keys():
        logger.info('User '+model.fingerprint+' connected to server.')
        server.connections[model.fingerprint] = Connection()
        for u in server.users.keys():
            if server.users[u].connection == model.fingerprint:
                server.connections[model.fingerprint].user = server.users[u]
                server.connections[model.fingerprint].logged_in = True
    return {}

class LoginModel(BaseModel):
    fingerprint: str
    username: str
    hashword: str
@app.post('/server/login/',tags=['server']) # Logs into server
async def login(model: LoginModel, response: Response):
    if not model.fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    
    logger.info('User '+model.fingerprint+' logging in.')

    uid = None
    for user in server.users.keys():
        if server.users[user].username == model.username:
            uid = user
            break

    if uid != None:
        if model.hashword == server.users[uid].password_hash:
            server.users[uid].connection = model.fingerprint
            server.connections[model.fingerprint].user = server.users[uid]
            server.connections[model.fingerprint].logged_in = True
            logger.info('Logged in: '+model.username)
            server.users[uid].update()
            return {'result':'Success.'}
        else:
            response.status_code = status.HTTP_403_FORBIDDEN
            return {'result':'Incorrect email or password.'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Email does not have an associated account.'}
@app.post('/server/login/new/',tags=['server']) # Adds new account, or logs in if one already exists
async def new_user(model: LoginModel, response: Response):
    if not model.fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    logger.info('User '+model.fingerprint+' creating new acct.')
    uid = None
    for user in server.users.keys():
        if server.users[user].username == model.username:
            uid = user
            break

    if uid != None:
        if model.hashword == server.users[model.username].password_hash:
            server.users[uid].connection = model.fingerprint
            server.connections[model.fingerprint].user = server.users[uid]
            server.connections[model.fingerprint].logged_in = True
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
        server.users[uid].update()
        return {'result':'Success.','uid':uid}
@app.post('/server/login/exit/',tags=['server']) # Logs out
async def logout(model: ConnectionModel, response: Response):
    if not model.fingerprint in server.connections.keys():
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'result':'Connection not found for user.'}
    
    if server.connections[model.fingerprint].logged_in:
        server.connections[model.fingerprint].user.connection = None
        server.connections[model.fingerprint].user = User('','','',cache=False)
        server.connections[model.fingerprint].logged_in = False
        logger.info('User '+model.fingerprint+' logged out.');
        return {'result':'Success.'}
    else:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return {'result':'User is not logged in.'}


# Client Endpoints




# Load web server
files = list(os.walk('client'))

slashtype = '/'
aux = '/'
if sys.platform == 'win32':
    slashtype = '\\'
    aux = '\\\\'

for f in files:
    split_path = f[0].split(slashtype)
    if len(split_path) > 1:
        new_path = '/'.join(split_path[1:])+'/'
    else:
        new_path = ''
    
    dirpath = aux.join(f[0].split(slashtype))

    for fn in f[2]:
        ext = os.path.splitext(fn)[1]
        code = '\n'.join([
            '@app.get("/'+new_path+fn+'", include_in_schema=False)',
            'async def web_'+fn.replace('.','_').replace('-','_').replace(' ','_').replace('\'','').replace('"','')+'():',
            '\treturn FileResponse("'+dirpath+aux+fn+'")'
        ])
        exec(
            code,
            globals(),
            locals()
        )

# Load periodic functions
@app.on_event('startup')
@repeat_every(seconds=5)
def check_connections_task():
    newconn = {}
    oldconn = server.connections.copy()
    for conn in oldconn.keys():
        if oldconn[conn].timeout >= time.time():
            newconn = oldconn[conn]
        else:
            logger.info('Timed out connection '+conn)
    server.connections = newconn.copy()



if __name__ == "__main__":
    uvicorn.run('main:app', host="127.0.0.1", port=5000, log_level="info", access_log=False)
