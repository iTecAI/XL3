import requests,json,markdown2

EXTRAS = [
    'break-on-newline',
    'cuddled-lists',
    'header-ids',
    'nofollow',
    'strike',
    'target-blank-links',
    'tables'
]

if __name__ == "__main__":
    from api_utils import *
else:
    from api.api_utils import *

def get5e_direct(endpoint,passed={},limit=0,**kwargs):
    full = []
    page = 1
    while True:
        payload = passed.copy()
        for k in kwargs.copy().keys():
            payload[k] = kwargs.copy()[k]
        payload['page'] = str(page)

        response = requests.get('https://api.open5e.com/'+endpoint+'/',params=payload)
        for i in response.json()['results']:
            full.append(i)
            if limit != 0 and len(full) >= limit:
                return full
        if response.json()['next'] == None:
            break
        page += 1
    return full

def get5e(endpoint,limit=0,search=''):
    full = []
    if os.path.exists(os.path.join('database','cached','open5e',endpoint+'.json')):
        with open(os.path.join('database','cached','open5e',endpoint+'.json'),'r') as f:
            data = json.load(f)
            for item in data:
                if search in item['slug']:
                    full.append(item)
                if len(full) >= limit and limit > 0:
                    return full
        return full
    else:
        raise ValueError('Endpoint is incorrect or does not exist in database.')

def get_section(section,to_html=True):
    out = None
    if os.path.exists(os.path.join('database','cached','open5e','sections.json')):
        with open(os.path.join('database','cached','open5e','sections.json'),'r') as f:
            data = json.load(f)
            for item in data:
                if section == item['slug']:
                    out = item

        if out:
            if to_html:
                return markdown2.markdown(out['desc'].replace('*\n|','*\n\n|'),extras=EXTRAS)
            else:
                return out['desc']
        else:
            raise ValueError('Could not fetch section '+section+' as it does not exist.')
        

def get_creatures(limit=0,search=''):
    results = get5e('monsters',limit=limit,search=search)
    creatures = {}
    for result in results:
        creatures[result['name']] = Creature5e(data=result)
    return creatures

class Creature5e(Creature):
    def get_creature_info(self, kwargs):
        self.src = 'open5e'
        return kwargs['data']
        
