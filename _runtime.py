import configparser, os
CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join('config','server.config'))

class Server:
    def __init__(self):
        self.connections = {}
        self.users = {}
        self.characters = {}
        self.campaigns = {}
server = Server()