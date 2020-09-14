import json,os
def split_on(string,seps):
    ret = string.split(seps.pop())
    for sep in seps:
        nret = []
        for item in ret:
            nret.extend(item.split(sep))
        ret = nret[:]
    return ret

with open(os.path.join('api','static_data','weapons.json'),'r') as f:
    dat = json.load(f)

out = []
for i in dat:
    d = {}
    d['name'] = i['name']
    d['slug'] = i['slug']
    d['group'] = i['category'].split(' ')[0].lower()
    d['type'] = i['category'].split(' ')[1].lower()
    cst = i['cost'].split(' ')
    if cst[1] == 'cp':
        d['cost'] = float(cst[0]) * 0.01
    elif cst[1] == 'sp':
        d['cost'] = float(cst[0]) * 0.1
    elif cst[1] == 'ep':
        d['cost'] = float(cst[0]) * 0.5
    elif cst[1] == 'gp':
        d['cost'] = float(cst[0])
    elif cst[1] == 'pp':
        d['cost'] = float(cst[0]) * 10.0
    d['damage'] = {
        'dice':i['damage_dice'],
        'type':i['damage_type']
    }
    d['weight'] = eval(i['weight'].strip(' lb.'))
    d['properties'] = []
    if i['properties']:
        for x in i['properties']:
            pd = {}
            parts = split_on(x,[' (',')'])
            pd['name'] = parts[0]
            if len(parts) > 1:
                if ' ' in parts[1]:
                    pd[parts[1].split(' ')[0]] = parts[1].split(' ')[1]
                else:
                    pd['value'] = parts[1]
            d['properties'].append(pd)
    out.append(d)
    
with open(os.path.join('api','static_data','weapons.json'),'w') as f:
    json.dump(out,f,indent=4)