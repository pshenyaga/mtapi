# mtapi.py
import sys
import re
import binascii
import hashlib
import asyncio
from protocol import Protocol

class Mtapi():
    def __init__(self, loop):
        self.loop = loop
        self.proto = None
        self.current_tag = 0
        self.to_resolve = {}

    def _next_tag(self):
        self.current_tag = self.current_tag + 1 if self.current_tag <= 65536 else 0
        return self.current_tag

    async def connect(self, **params):
        '''Connect to the router
        params: {'host': 'hostname',
                 'port': 'portnamber',
                 'user': 'username',
                 'pass': 'password'}'''
        params = {
            'host': params.get('host', '192.168.88.1'),
            'port': params.get('port', 8728),
            'user': params.get('user', 'admin'),
            'pass': params.get('pass', '')
        }
        try:
            reader, writer = await asyncio.open_connection(
                params['host'],
                params['port'],
                loop=self.loop)
            self.proto = Protocol(reader, writer)
        except:
            proto = None
            print("Error in connect")
            # TODO
            # raise or propogate connection error
        self.loop.create_task(self.read_response())
        await self.login(params['user'], params['pass'])

    def send(self, command, *params):
        tag = self._next_tag()
        self.to_resolve[tag] = asyncio.Future(loop=loop)
        self.proto.write_sentence(command, *params, '.tag={}'.format(tag))
        return self.to_resolve[tag]


    def _parse_response_attrs(self, start, sentence):
        attrs = {}
        #print(sentence)
        for n in range(1, len(sentence)):
            if re.search("^\.", sentence[n]):
                attr = sentence[n].split('=')
            else:
                attr = sentence[n].split('=', 2)[1:]
            attrs.update({attr[0]: attr[1]})
        return attrs

    async def read_response(self):
        response = {}
        while True:
            sentence = await self.proto.read_sentence()
            attrs = self._parse_response_attrs(1, sentence)
            tag = int(attrs['.tag'])
            if tag in response.keys():
                response[tag].append((sentence[0], attrs))
            else:
                response[tag] = [(sentence[0], attrs)]
            if sentence[0] == '!done':
                self.to_resolve[tag].set_result(response[tag])
    
    async def talk(self, command, *attrs):
        # Talk to remote
        future = self.send(command, *attrs)
        # Await response
        await asyncio.wait_for(future, timeout=5)
        # TODO
        # remove future from self.to_resolve
        return future.result()
       # try:
        #sentence = await asyncio.wait_for(self._read_sentence(), timeout = 5) 
       # except:
       #     print("No response in talk")
    
    async def login(self, user, password):
        '''Login to the router'''
        sentence = ('/login', '=name=' + user, '=password=' + password)
        login_response = await self.talk(*sentence)
        for replay, attrs in login_response:
            if replay == '!trap':
                #TODO
                # Error handling for auth
                print(attrs['message'])
            if 'ret' in attrs:
                # RouterOs pre-v6.43
                login_response2 = await self.talk("/login",
                    "=name=" + user,
                    "=response=00" + auth_response(password, attrs['ret']))
                for replay2, attrs2 in login_response2:
                    if replay2 == '!trap':
                        #TODO
                        # Error handling for auth
                        print(attrs2['message'])

    def _auth_response(pwd, ret):
        chal = binascii.unhexlify(ret.encode(sys.stdout.encoding))
        md = hashlib.md5()
        md.update(b'\x00')
        md.update(pwd.encode(sys.stdout.encoding))
        md.update(chal)
        return binascii.hexlify(md.digest()).decode(sys.stdout.encoding)

if __name__ == '__main__':
    params = {
        'host': '10.253.1.5',
        'port': '8728',
        'user': 'api',
        'pass': 'api_hard_pass'
    }
    
    loop = asyncio.get_event_loop()
    api = Mtapi(loop)

    async def test():
        await asyncio.wait_for(api.connect(**params), timeout=5)
        result = await asyncio.wait_for(api.talk(
            '/ip/address/print'), timeout = 5)
        for res in result:
            print(res)

    try:
        loop.run_until_complete(test())
    except KeyboardInterrupt:
        loop.close()
        
