import d20, re, json
import pickle
import os.path
from api.open5e import get5e_direct, get5e, get_creatures, get_section
from api.api_utils import *
from api.character_models import *
from api.pycritter import *
from api.images import *
from _runtime import server, CONFIG
import logging
logger = logging.getLogger("uvicorn.error")

def cond(c,t,f):
    if c:
        return t
    else:
        return f

def chatbot_interpret(content,fingerprint,campaign,map):
    raw_split = content.split(' ')
    cmd = raw_split[0]
    args = [{'name':'__main__','value':[]}]
    if len(raw_split) > 1:
        _args = raw_split[1:]
        current = 0
        for a in _args:
            if a.startswith('-') and len(a) > 1:
                args.append({'name':a[1:],'value':[]})
                current += 1
            else:
                args[current]['value'].append(a)
    args = [{'name':i['name'],'value':' '.join(i['value'])} for i in args]
    args[0]['value'] = args[0]['value'].split(' ')

    logger.info(f'User {fingerprint} sent command {cmd} with args {str(args)} to map {map} in campaign {campaign}')

    if cmd in ['r','roll']:
        roll_args = []
        jnr = ''
        for i in args[0]['value'][0]:
            jnr += i
            if i in ['+','-','*','/']:
                roll_args.append(jnr)
                jnr = ''
        if len(jnr) > 0:
            roll_args.append(jnr)

        if 'adv' in args[0]['value']:
            c = 0
            for arg in roll_args:
                if 'd' in arg:
                    roll_args[c] = '2d'+roll_args[c].split('d')[1][:len(roll_args[c].split('d')[1])-1]+'kh1'+cond(roll_args[c].split('d')[1][len(roll_args[c].split('d')[1])-1] in ['+','-','*','/'], roll_args[c].split('d')[1][len(roll_args[c].split('d')[1])-1],'')
                c+=1
        elif 'dis' in args[0]['value']:
            c = 0
            for arg in roll_args:
                if 'd' in arg:
                    roll_args[c] = '2d'+roll_args[c].split('d')[1][:len(roll_args[c].split('d')[1])-1]+'kl1'+cond(roll_args[c].split('d')[1][len(roll_args[c].split('d')[1])-1] in ['+','-','*','/'], roll_args[c].split('d')[1][len(roll_args[c].split('d')[1])-1],'')
                c+=1
        roll_args = ''.join(roll_args)
        return str(d20.roll(roll_args))