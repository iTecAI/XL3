import requests,json

if __name__ == "__main__":
    from api_utils import *
else:
    from api.api_utils import *

def get5e(endpoint,passed={},**kwargs):
    full = []
    page = 1
    while True:
        payload = passed.copy()
        for k in kwargs.copy().keys():
            payload[k] = kwargs.copy()[k]
        payload['page'] = str(page)

        response = requests.get('https://api.open5e.com/'+endpoint+'/',params=payload)
        print(response.url)
        full.extend(response.json()['results'])
        if response.json()['next'] == None:
            break
        page += 1
    return full

def get_creatures(**kwargs):
    results = get5e('monsters',kwargs)
    creatures = {}
    for result in results:
        creatures[result['name']] = Creature5e(data=result)
    return creatures

class Creature5e(Creature):
    def get_creature_info(self, kwargs):
        return kwargs['data']

'''dat = get_creatures(type='celestial')
#print('\n\n======\n\n'.join([i+':\n\n'+dat[i].json(indent=4) for i in dat.keys()]))
with open('out.json','w') as f:
    json.dump({i:dat[i].to_dict() for i in dat.keys()},f,indent=4)'''


        
