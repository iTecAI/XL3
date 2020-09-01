from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import rsa
import os
import sys

# Configs
VERSION = 0

# Classes
class Server:
    def __init__(self,state=None):
        if state:
            pass
        else:
            self.connections = {}

# App

server = Server() # Instantiate server instance - todo add stateful cache
app = FastAPI()
    
'''@app.get('/')
async def root():
    with open(os.path.join('client','index.html'),'r') as f:
        return f.read()'''
    
@app.get('/server/connection/status/{connection}')
async def conn_status(connection):
    return {'connection':server.connections}


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
        code = '\n'.join([
            '@app.get("/'+new_path+fn+'", response_class=HTMLResponse)',
            'async def web_'+fn.replace('.','_')+'():',
            '\twith open("'+dirpath+aux+fn+'","r") as f:',
            '\t\treturn f.read()'
        ])
        print(code)
        exec(
            code,
            globals(),
            locals()
        )




if __name__ == "__main__":
    uvicorn.run('main:app', host="127.0.0.1", port=5000, log_level="info")
