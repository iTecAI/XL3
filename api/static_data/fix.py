import json,os
def split_on(string,seps):
    ret = string.split(seps.pop())
    for sep in seps:
        nret = []
        for item in ret:
            nret.extend(item.split(sep))
        ret = nret[:]
    return ret

with open(os.path.join('api','static_data','equipment.json'),'r') as f:
    dat = json.load(f)
with open(os.path.join('api','static_data','weapons.json'),'r') as f:
    datw = json.load(f)

for i in datw:
    dat.append({
        'slug':i['slug'],
        'cost':i['cost'],
        'weight':i['weight'],
        'quantity':1,
        'name':i['name']
    })
    
with open(os.path.join('api','static_data','equipment.json'),'w') as f:
    json.dump(dat,f,indent=4)