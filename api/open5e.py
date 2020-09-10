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
        self.src = 'open5e'
        return kwargs['data']


        
