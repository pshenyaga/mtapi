# blockedapi.py
import asyncio
from mtapi import asyncapi
from mtapi import error as mterror

def connect(address, port, user, password):
    '''Try to connect and to login to the router. If success - returns blocked
    API object.
        Usage:
            api = blockedapi.connect(address, port, user, password)'''

    api = API()
    try:
        api.connect(address, port)
    except:
        raise
    else:
        try:
            api.login(user, password)
        except:
            raise
        else:
            return api


class API:
     
    _loop = asyncio.get_event_loop()

    def __init__(self):
        self.api = asyncapi.API(API._loop)


    def connect(self, address, port):
        '''Try to connect to the given router. If an error occurred - raise it.
            Usage:
                api = blockedapi.connect(address, port)'''
        try:
            API._loop.run_until_complete(
                self.api.connect(address, port))
        except:
            raise


    def login(self, user, password):
        try:
            API._loop.run_until_complete(
                self.api.login(user, password))
        except:
            raise


    def talk(self, command, *args):
        try:
            result = API._loop.run_until_complete(
                self.api.talk(command, *args))
        except:
            raise
        else:
            return result


    def close(self):
        try:
            API._loop.run_until_complete(
                self.api.close())
        except:
            raise
