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

for i in range(len(dat)):
    if dat[i]['quantity'] > 1:
        dat[i]['weight'] = dat[i]['weight'] / dat[i]['quantity']
        dat[i]['cost'] = dat[i]['cost'] / dat[i]['quantity']
    
with open(os.path.join('api','static_data','equipment.json'),'w') as f:
    json.dump(dat,f,indent=4)