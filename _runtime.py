class Server:
    def __init__(self,state=None):
        if state:
            pass
        else:
            self.connections = {}
            self.users = {}
server = Server()