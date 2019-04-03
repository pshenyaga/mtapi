# mtapi.py
import sys
import re
import binascii
import hashlib
import asyncio
import logging
from protocol import Protocol
from contextlib import suppress

class Error(Exception):
    """Base class for exceptions in mtapi module"""
    pass

class FatalError(Error):
    pass

class Mtapi():
    def __init__(self, loop):
        self.loop = loop
        self.loop.set_debug(True)
        self.reader_task = None
        self.proto = None
        self.current_tag = 0
        self.to_resolve = {}
        #---- Temporary logger config
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger('asyncio')
        self.logger.setLevel(logging.DEBUG)
        #self.ch = logging.StreamHandler()
        #self.logger.addHandler(self.ch)
        #---- Temporary logger end

    def _next_tag(self):
        self.current_tag = self.current_tag + 1 if self.current_tag <= 65536 else 0

        return self.current_tag

    def send(self, command, *params):
        tag = self._next_tag()
        self.to_resolve[tag] = asyncio.Future(loop=loop)
        self.proto.write_sentence(command, *params, '.tag={}'.format(tag))

        return self.to_resolve[tag]

    def _parse_response_attrs(self, sentence):
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
        def stop(self, error):
            # clean up all
            self.writer.close()
            for future in self.to_resolve.values():
                future.set_exception(error)
            raise asyncio.CancelledError

        response = {}
        while True:
            try:
                sentence = await self.proto.read_sentence()
            except asyncio.streams.IncompleteReadError as e:
                #expected = e.expected
                #message = "Connection closed when reading {} bytes.".format(e.expected)
                self.logger.error(e)
                stop(self, FatalError(e))
            except asyncio.CancelledError as e:
                self.logger.debug("Reader task cancelled")
                stop(self, e)
            if sentence[0] == '!fatal':
                # Nothig to do. Connection is closed.
                self.logger.error('Connection closed!')
                stop(self, FatalError("'!fatal' received. Connection closed."))

            attrs = self._parse_response_attrs(sentence)
            tag = int(attrs.pop('.tag'))
            if tag in response.keys():
                response[tag].append((sentence[0], attrs))
            else:
                response[tag] = [(sentence[0], attrs)]
            if sentence[0] == '!done':
                response[tag].pop()
                self.to_resolve[tag].set_result((tag, response[tag]))
    
    async def talk(self, command, *attrs):
        future = self.send(command, *attrs)
        try:
            await future
        except:
            raise
        else:
            tag, result = future.result()
            del self.to_resolve[tag]

            return(result)
    
    async def login(self, user, password):
        '''Login to the router'''

        def _auth_response(pwd, ret):
            chal = binascii.unhexlify(ret.encode(sys.stdout.encoding))
            md = hashlib.md5()
            md.update(b'\x00')
            md.update(pwd.encode(sys.stdout.encoding))
            md.update(chal)

            return binascii.hexlify(md.digest()).decode(sys.stdout.encoding)

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
        reader, writer = await asyncio.open_connection(
            params['host'],
            params['port'],
            loop=self.loop)
        self.writer = writer
        self.proto = Protocol(reader, writer)
        self.reader_task = self.loop.create_task(self.read_response())
        await self.login(params['user'], params['pass'])

    async def close(self):
        if not self.reader_task.cancelled():
            self.reader_task.cancel()
        while not self.reader_task.cancelled():
            await asyncio.sleep(0.01)
            self.logger.debug("Mtapi.close(): Wating for reader task")
        print("Goodbye!")

if __name__ == '__main__':
    params = {
        'host': '10.253.12.130',
        'port': '8728',
        'user': 'api',
        'pass': 'api_hard_pass'
    }
    
    loop = asyncio.get_event_loop()
    api = Mtapi(loop)

    async def test():
        try:
            await asyncio.wait_for(api.connect(**params), timeout=5)
        except FatalError as e:
            print("Connection closed.")
        except asyncio.futures.TimeoutError:
            print("Time out.")
        except OSError as e:
            print(e)
        else:
            try:
            #    result = await asyncio.wait_for(api.talk(
                result = await api.talk(
                    '/ip/firewall/address-list/print', '?list=ADM-HOSTS')
                    #'/interface/print'), timeout = 5)
                    #'/interface/print', '?name=hw00'), timeout = 5)
                    #'/ip/firewall/address-list/print'), timeout = 5)
            except FatalError as e:
                print(e)
            except asyncio.futures.TimeoutError as e:
                print("Timeout!!!")
            else:
                for res in result:
                    print(res)
        finally:
            await api.close()



    try:
        loop.run_until_complete(test())
    except KeyboardInterrupt:
        loop.close()
        
