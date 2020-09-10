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

def get5e(endpoint,passed={},limit=0,**kwargs):
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

def get_section(section,to_html=True):
    try:
        if to_html:
            return markdown2.markdown(requests.get('https://api.open5e.com/sections/'+section+'/').json()['desc'],extras=EXTRAS)
        else:
            return requests.get('https://api.open5e.com/sections/'+section+'/').json()['desc']
    except KeyError:
        raise ValueError('Could not fetch section '+section+' as it does not exist.')

def get_creatures(**kwargs):
    results = get5e('monsters',kwargs)
    creatures = {}
    for result in results:
        creatures[result['name']] = Creature5e(data=result)
    return creatures

class Creature5e(Creature):
    def get_creature_info(self, kwargs):
        self.src = 'open5e'
        return kwargs['data']
        
