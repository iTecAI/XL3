import json

class Character:
    def __init__(self,**kwargs):
        pass
    def to_dict(self):
        items = [
            'name','race','class_display','classes','level','xp','prof','speed',
            'alignment','ac','max_hp','hp','init','attacks','abilities','skills',
            'other_profs','spellcasting','resist','vuln','immune'
            ]
        return {i:getattr(self,i,None) for i in items}

    def to_json(self,indent=None):
        return json.dumps(self.to_dict(),indent=indent)