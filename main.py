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
from classes import *
import urllib
import logging
import base64
import json
import random
import time
import pickle
from endpoints import server_endpoint
from _runtime import server

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
        with open(os.path.join('database',f,'registry.json'),'w') as reg:
            reg.write('{}')
    except FileExistsError:
        pass

'''Get OpenAPI configs'''
with open(os.path.join('config','openapi.json'),'r') as c:
    openapicfg = json.load(c)
    tags_meta =  openapicfg['metadata']

# App

 # Instantiate server instance - todo add stateful cache
app = FastAPI(openapi_tags=tags_meta)

# Routers

app.include_router(
    server_endpoint.router,
    prefix='/server',
    tags=['server']
)

@app.get('/', response_class=HTMLResponse, include_in_schema=False) # Get index.html when navigated to root
async def root():
    with open(os.path.join('client','index.html'),'r') as f:
        return f.read()

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

# Start tasks
@app.on_event('startup')
async def load_users():
    reg = get_user_registry()
    for u in reg.keys():
        if os.path.exists(os.path.join('database','users',u+'.pkl')):
            server.users[u] = os.path.join('database','users',u+'.pkl')

# Load periodic functions
@app.on_event('startup')
@repeat_every(seconds=5)
async def check_connections_task():
    newconn = {}
    oldconn = server.connections.copy()
    for conn in oldconn.keys():
        if oldconn[conn].timeout >= time.time():
            newconn = oldconn[conn]
        else:
            logger.info('Timed out connection '+conn)
            cache_user(server.connections[conn].uid)
    server.connections = newconn.copy()



if __name__ == "__main__":
    uvicorn.run('main:app', host="127.0.0.1", port=5000, log_level="info", access_log=False)
