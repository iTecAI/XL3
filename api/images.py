import os, secrets, json, base64

def add_image(data):
    iid = secrets.token_urlsafe(32)
    dat = data.split(';base64,')[1]
    ft = data.split(';base64,')[0].split('/')[1]
    if not ft in ['png','jpg','jpeg','bmp']:
        raise ValueError("File type must fall within ['png','jpg','jpeg','bmp']")
    with open(os.path.join('database','images',iid+'.'+ft),'wb') as f:
        f.write(base64.b64decode(dat.encode('utf-8')))
    with open(os.path.join('database','images','registry.json'),'r') as f:
        r = json.load(f)
    r[iid] = {'path':os.path.join('database','images',iid+'.'+ft),'filetype':ft}
    with open(os.path.join('database','images','registry.json'),'w') as f:
        f.write(json.dumps(r))
    return iid

def del_image(iid):
    with open(os.path.join('database','images','registry.json'),'r') as f:
        r = json.load(f)
    if iid in r.keys():
        os.remove(r[iid]['path'])
        del r[iid]
        with open(os.path.join('database','images','registry.json'),'w') as f:
            f.write(json.dumps(r))
    else:
        raise KeyError(f'Image with IID {iid} does not exist.')