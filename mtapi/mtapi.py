# mtapi.py
import sys
import socket
import binascii
import hashlib
import asyncio

class Mtapi(asyncio.Protocol):
    def __init__(self, loop=None):
        self.loop = loop
        self.password = password
        self.transport = None
        self.data_future = self.loop.create_future()

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        sentences = []
        while len(data):
            sentence, data = self._read_sentence(data)
            if sentence[-1]:
                # Partial sentence received
                pass
            else:
                sentences.append(sentence)
        self.data_future.set_result(sentences)

    def connection_lost(self, ext):
        pass

    def _write_sentence(self, *words):
        '''Send sentence to the router'''
        words = list(words)
        words.append('')
        sentence = bytes()
        for word in words:
            sentence += self._encode_word(word)
        self.transport.write(sentence)
    
    def _encode_word(self, word):
        '''Write world to the router'''
        enc_len = self._encode_len(len(word))

        return enc_len + word.encode('latin1')
    
    def _write_bytes(self, bytes_to_write):
        '''Write bytes to the router'''
        # TODO: Error handling for write
        self.transport.write(bytes_to_write)
    
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

    def _read_sentence(self, data):
        '''Read sentence'''
        words = []
        while len(data):
            word, data = self._read_word(data)
            words.append(word)
            if len(word) == 0:
                break
        return words, data

    def _read_word(self, data):
        len_, data = self._decode_length(data)
        word = data[:len_]
        data = data[len_:]
        return word.decode('latin1'), data

    def _decode_length(self, data):
        def decode_low_bytes(len_, lower_bytes):
            for byte in low_bytes:
                len_ <<= 8
                len_ += byte
            return len_

        #len_ = ord(data[0])
        len_ = data[0]
        data = data[1:]
        if (len_ & 0x80) == 0x00:
            pass
        elif(len_ & 0xC0) == 0x80:
            len_ &= ~0xC0
            low_bytes = data[0]
            data = data[1:]
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xE0) == 0xC0:
            len_ &= ~0xE0
            low_bytes = data[:2]
            data = data[2:]
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xF0) == 0xE0:
            len_ &= ~0xF0
            low_bytes = data[:3]
            data = data[3:]
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xF8) == 0xF0:
            low_bytes = data[:4]
            data = data[4:]
            low_bytes = read_bytes(sock, 4)
            len_ = decode_low_bytes(0, low_bytes)
        else:
            # Can't be decoded
            # TODO: generate extension
            pass

        return len_, data
    
    async def login(self, user, password):
        sentence = ('/login', '=name=' + user, '=password=' + password)
        login_response = await self.talk(*sentence)
        print(login_response)

    async def talk(self, command, *params):
        # Talk to remote
        self._write_sentence(command, *params)
        # Await response
        await asyncio.wait_for(self.data_future, timeout = 5) 
        return self.data_future.result()

#def connect(**params):
#    '''Connect to the router
#       params: {'host': 'hostname',
#                'port': 'portnamber',
#                'user': 'username',
#                'pass': 'password'}'''
#    conn_params = {'host': params.get('host', '192.168.88.1'),
#                   'port': params.get('port', 8728),
#                   'user': params.get('user', 'admin'),
#                   'pass': params.get('pass', '')}
    
#    # create socket
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.settimeout(2)
#    # connect to the router
#    # TODO: error handling for connection
#    sock.connect((conn_params['host'], conn_params['port']))
#    return sock
#    # 2. login
#    # login(sock, conn_params['user'], conn_params['pass'])

#def login(sock, user, password):
#    '''Login to the router'''
#    # talk to the router with login information
#    for replay, attrs in talk(sock, "/login", '=name=' + user, '=password=' + password):
#        if replay == '!trap':
#            # TODO: Error handling for auth
#            print(replay, attrs)
#        if 'ret' in attrs:
#            # RouterOs pre-v6.43
#            for replay2, attrs2 in talk(sock, "/login", "=name=" + user,
#                    "=response=00" + auth_response(password, attrs['ret'])):
#                if replay2 == '!trap':
#                    # TODO: Error handling for auth
#                    print(replay2, attrs2)

#def auth_response(pwd, ret):
#    chal = binascii.unhexlify(ret.encode(sys.stdout.encoding))
#    md = hashlib.md5()
#    md.update(b'\x00')
#    md.update(pwd.encode(sys.stdout.encoding))
#    md.update(chal)
#    return binascii.hexlify(md.digest()).decode(sys.stdout.encoding)

#def talk(sock, command, *params):
#    '''Send sentence to the router and read response'''
#    response = []
#    write_sentence(sock, command, *params)
#    # while first world != '!done'
#    while True:
#        sentence = read_sentence(sock)
#        attrs = {}
#        for n in range(1, len(sentence)):
#            attr = sentence[n].split('=', 2)[1:]
#            attrs.update({attr[0]: attr[1]})
#        response.append((sentence[0], attrs))
#        if sentence[0] == '!done':
#            return response

if __name__ == '__main__':

    dst_host = '10.253.1.5' 
    dst_port = '8728'
    user = 'api'
    password = 'api_hard_pass'
    loop = asyncio.get_event_loop()
    api = Mtapi(loop)

    async def connect():
        await asyncio.wait_for(
            loop.create_connection(
                lambda: api, dst_host, dst_port),
            timeout = 5)
        await asyncio.wait_for(
            api.login(user, password),
            timeout = 5)
    try:
        loop.run_until_complete(connect())
    except KeyboardInterrupt:
        loop.close()
