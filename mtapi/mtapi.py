# mtapi.py
import sys
import socket
import binascii
import hashlib
import asyncio

class Mtapi():
    def __init__(self, loop):
        self.loop = loop
        self.reader = None
        self.writer = None

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
            self.reader, self.writer = await asyncio.open_connection(
                params['host'],
                params['port'],
                loop=self.loop)
            await self._login(params['user'], params['pass'])
        except:
            self.reader = None
            self.writer = None
            print("Error in connect")
            # TODO
            # raise or propogate connection error

    def _write_sentence(self, *words):
        '''Send sentence to the router'''
        words = list(words)
        words.append('')
        sentence = bytes()
        for word in words:
            sentence += self._encode_word(word)
        self.writer.write(sentence)
    
    def _encode_word(self, word):
        '''Write world to the router'''
        enc_len = self._encode_len(len(word))

        return enc_len + word.encode('latin1')
    
    def _encode_len(self, length):
        '''Encode len'''
        enc_len = bytes()
        if length <= 0x7F:
            enc_len += length.to_bytes(1, sys.byteorder)
        elif length <= 0x3FFF:
            length |= 0x8000
            enc_len += (length >> 8).to_bytes(1, sys.byteorder)
            enc_len += (length & 0xFF).to_bytes(1, sys.byteorder)
        elif length <= 0x1FFFFF:
            length |= 0xC00000
            enc_len += (length >> 16).to_bytes(1, sys.byteorder)
            enc_len += ((length >> 8) & 0xFF).to_bytes(1, sys.byteorder)
            enc_len += (length & 0xFF).to_bytes(1, sys.byteorder)
        elif length <= 0xFFFFFFF:
            length |= 0xE0000000
            enc_len += (length >> 24).to_bytes(1, sys.byteorder)
            enc_len += ((length >> 16) & 0xFF).to_bytes(1, sys.byteorder)
            enc_len += ((length >> 8) & 0xFF).to_bytes(1, sys.byteorder)
            enc_len += (length & 0xFF).to_bytes(1, sys.byteorder)
        elif length <= 0xFFFFFFFF:
            enc_len += 0xF0.to_bytes(1, sys.byteorder)
            enc_len += ((length >> 24) & 0xFF).to_bytes(1, sys.byteorder)
            enc_len += ((length >> 16) & 0xFF).to_bytes(1, sys.byteorder)
            enc_len += ((length >> 8) & 0xFF).to_bytes(1, sys.byteorder)
            enc_len += (length & 0xFF).to_bytes(1, sys.byteorder)
        else:
            # len too big
            # TODO: generate extension
            pass

        return enc_len

    async def _read_sentence(self):
        '''Read sentence'''
        words = []
        while True:
            word = await self._read_word()
            if len(word) == 0:
                break
            words.append(word)
        return words

    async def _read_word(self):
        len_ = await self._read_length()
        #TODO
        # read exactly len_ bytes
        word = await self.reader.read(len_)
        return word.decode('latin1')

    async def _read_length(self):
        def decode_low_bytes(len_, lower_bytes):
            for byte in low_bytes:
                len_ <<= 8
                len_ += byte
            return len_

        len_ = ord(await self.reader.read(1))
        if (len_ & 0x80) == 0x00:
            pass
        elif(len_ & 0xC0) == 0x80:
            len_ &= ~0xC0
            low_bytes = await self.reader.read(1)
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xE0) == 0xC0:
            len_ &= ~0xE0
            low_bytes = await self.reader.read(2)
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xF0) == 0xE0:
            len_ &= ~0xF0
            low_bytes = await self.reader.read(3)
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xF8) == 0xF0:
            low_bytes = await self.reader.read(4)
            len_ = decode_low_bytes(0, low_bytes)
        else:
            # Can't be decoded
            # TODO: raise extension
            pass

        return len_
    
    async def talk(self, command, *params):
        response = []
        # Talk to remote
        self._write_sentence(command, *params)
        # Await response
        while True:
            sentence = await self._read_sentence()
            if sentence[0] == '!done':
                return response
            attrs = {}
            for n in range(1, len(sentence)):
                attr = sentence[n].split('=', 2)[1:]
                attrs.update({attr[0]: attr[1]})
            response.append((sentence[0], attrs))
       # try:
        #sentence = await asyncio.wait_for(self._read_sentence(), timeout = 5) 
       # except:
       #     print("No response in talk")
    
    async def _login(self, user, password):
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

    def auth_response(pwd, ret):
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
        'password': 'api_hard_pass'
    }
    
    loop = asyncio.get_event_loop()
    api = Mtapi(loop)

    #async def connect():
    #    await asyncio.wait_for(
    #        loop.create_connection(
    #            lambda: api, dst_host, dst_port),
    #        timeout = 5)
    #    await asyncio.wait_for(
    #        api.login(user, password),
    #        timeout = 5)
    
    try:
        loop.run_until_complete(api.connect(**params))
    except KeyboardInterrupt:
        loop.close()
