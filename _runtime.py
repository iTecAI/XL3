import configparser, os
CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join('config','server.config'))

class Server:
    def __init__(self):
        self.connections = {}
        self.users = {}
        self.characters = {}
        self.campaigns = {}
        self.updates = {
            'client':False,
            'characters':False,
            'campaigns':False
        }
    def check(self,u):
        v = self.updates.copy()[u]
        self.updates[u] = False
        return v

server = Server()