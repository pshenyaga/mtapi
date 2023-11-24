# api.py

from mtapi.protocol import Protocol
from mtapi import error as mt_error
import sys
import re
import binascii
import hashlib
import asyncio
import logging


async def connect(loop=None,
                  address: str="192.168.88.1",
                  port: str="8728",
                  username: str="admin",
                  password: str="",
                  debug: bool=False,
                  **params: any):
    '''Connect and login to the router. Returns HlAPI object.
    Usage:
        my_router = hlapia.connect(loop="my_event_loop",
                                   address="my_router_address",
                                   port="my_router_port",
                                   username="my_username",
                                   password="my_hard_pass")'''

    api = API(loop)
    api.set_debug(debug)
    try:
        await api.connect(address, port)
    except:
        raise
    else:
        try:
            await api.login(username, password)
        except:
            await api.close()
            raise
        else:
            return api


class API:
    def __init__(self, loop):
        self.loop = loop
        self.host = None
        self.port = None
        self.reader_task = None
        self.proto = None
        self.current_tag = 0
        self.to_resolve = {}
        self._debug = False
        self.logger = logging.getLogger('mtapi')

    def set_debug(self, debug=False):
        self._debug = debug
        #self.loop.set_debug(debug)
        #logging.basicConfig(level=logging.DEBUG)
        # self.logger = logging.getLogger('asyncio')
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def _next_tag(self):
        self.current_tag = self.current_tag + 1 if self.current_tag <= 65536 else 0

        return self.current_tag

    def send(self, command, *params):
        if len(command) == 0:
            return None

        tag = self._next_tag()

        self.logger.debug(
            '{}: Mtapi.send(): {} : {} {}' .format(
                 self.host,
                 tag,
                 command,
                 " ".join(params)))

        self.to_resolve[tag] = asyncio.Future(loop=self.loop)
        self.proto.write_sentence(command, *params, '.tag={}'.format(tag))

        return self.to_resolve[tag]

    async def read_response(self):
        def parse_response_attrs(sentence):
            attrs = {}
            for n in range(1, len(sentence)):
                if re.search("^\.", sentence[n]):
                    attr = sentence[n].split('=')
                else:
                    attr = sentence[n].split('=', 2)[1:]
                attrs.update({attr[0]: attr[1]})

            return attrs

        def stop(self, error):
            # clean up all
            self.writer.close()
            for future in self.to_resolve.values():
                if not future.done():
                    future.set_exception(error)
            raise asyncio.CancelledError

        response = {}
        while True:
            try:
                sentence = await self.proto.read_sentence()
#            except asyncio.streams.IncompleteReadError as e:
            except asyncio.IncompleteReadError as e:
                if self._debug:
                    self.logger.error("{}: {}".format(self.host, e))
                stop(self, mt_error.FatalError(e))
            except asyncio.CancelledError as e:
                if self._debug:
                    self.logger.debug("{}: Reader task cancelled".format(self.host))
                stop(self, e)
            if sentence[0] == '!fatal':
                if self._debug:
                    self.logger.error('{}: Connection closed!'.format(self.host))
                stop(self, mt_error.FatalError("'!fatal' received. Connection closed."))

            attrs = parse_response_attrs(sentence)
            tag = int(attrs.pop('.tag'))

            if self._debug:
                self.logger.debug(
                    '{}: Mtapi.read_response(): {} : {}'.format(
                        self.host,
                        tag,
                        sentence))

            if tag in response.keys():
                response[tag].append((sentence[0], attrs))
            else:
                response[tag] = [(sentence[0], attrs)]
            if sentence[0] == '!done':
#                if len(sentence) == 2:
#                    response[tag].pop()
                self.to_resolve[tag].set_result((tag, response[tag]))

    async def talk(self, command, *attrs):
        if self._debug:
            self.logger.debug(
                '{}: Mtapi.talk(): sended: {} {}'.format(
                    self.host,
                    command,
                    attrs))
        future = self.send(command, *attrs)
        if not future:
            return []
        try:
            await future
        except:
            raise
        else:
            tag, result = future.result()
            if self._debug:
                self.logger.debug(
                    '{}: Mtapi.talk(): received: {} {}'.format(
                        self.host,
                        tag,
                        result))
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

        login_response = await self.talk('/login',
                                         '=name=' + user,
                                         '=password=' + password)
        for replay, attrs in login_response:
            if replay == '!trap':
                error_message = "{{}".format(
                    attrs['message'])
                if self._debug:
                    self.logger.error(
                        '{}: Mtapi.login(): {}'.format(
                            self.host, error_message))
                raise mt_error.TrapError(error_message)
            if 'ret' in attrs:
                # RouterOs pre-v6.43
                login_response2 = await self.talk("/login",
                    "=name=" + user,
                    "=response=00" + _auth_response(password, attrs['ret']))
                for replay2, attrs2 in login_response2:
                    if replay2 == '!trap':
                        error_message = "{}".format(
                            attrs2['message'])
                        if self._debug:
                            self.logger.error(
                                '{}: Mtapi.login(): {}'.format(
                                    self.host,
                                    error_message))
                        raise mt_error.TrapError(error_message)

    async def connect(self,
                      address: str="192.168.88.1",
                      port: str=8728,
                      **params: any) -> None:
        '''Connect to the router
        Usage:
            connect("my_address", "my_port")'''

        try:
            reader, self.writer = await asyncio.open_connection(
                address,
                port,
                loop=self.loop)
        except:
            raise
        else:
            self.host, self.port = self.writer.get_extra_info('peername')
            self.proto = Protocol(reader, self.writer)
            self.reader_task = self.loop.create_task(self.read_response())

    async def close(self):
        if not self.reader_task:
            if self._debug:
                self.logger.debug(
                    "{}: Mtapi.close(): No reader task. Nothing to do.".format(self.host))
            return
        if not self.reader_task.cancelled():
            self.reader_task.cancel()
        attempts = 0
        while not self.reader_task.cancelled() and attempts < 3:
            await asyncio.sleep(0.01)
            self.logger.debug("{}: Mtapi.close(): Wating for reader task".format(self.host))
            attempts += 1

