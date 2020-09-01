from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
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

# Classes
class Server:
    def __init__(self,state=None):
        if state:
            pass
        else:
            self.connections: Connection = {}
            self.users: dict = {}

class Connection:
    def __init__(self):
        self.user = None

class User:
    def __init__(self,uid,usn,pswhash):
        self.uid = uid
        self.username = usn
        self.password_hash = pswhash

# App

server = Server() # Instantiate server instance - todo add stateful cache
app = FastAPI()
    
@app.get('/', response_class=HTMLResponse) # Get index.html when navigated to root
async def root():
    with open(os.path.join('client','index.html'),'r') as f:
        return f.read()
    
@app.get('/server/connection/status/{connection}/') # Get connection status
async def server_conn_status(connection):
    return {'connection':server.connections}

@app.post('/server/connection/new/') # Make new connection
async def server_conn_new(request: Request):
    data = parse(await request.body())
    if not data['fingerprint'] in server.connections.keys():
        server.connections[data['fingerprint']] = Connection()
    return {}


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
        if ext in []:
            code = '\n'.join([
                '@app.get("/'+new_path+fn+'", response_class=HTMLResponse)',
                'async def web_'+fn.replace('.','_').replace('-','_').replace(' ','_').replace('\'','').replace('"','')+'():',
                '\twith open("'+dirpath+aux+fn+'","r") as f:',
                '\t\treturn f.read()'
            ])
        else:
            code = '\n'.join([
                '@app.get("/'+new_path+fn+'")',
                'async def web_'+fn.replace('.','_').replace('-','_').replace(' ','_').replace('\'','').replace('"','')+'():',
                '\treturn FileResponse("'+dirpath+aux+fn+'")'
            ])
        exec(
            code,
            globals(),
            locals()
        )




if __name__ == "__main__":
    uvicorn.run('main:app', host="127.0.0.1", port=5000, log_level="debug")
