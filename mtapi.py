# mtapi.py
import sys, socket, binascii, hashlib

def connect(**params):
    '''Connect to the router
       params: {'host': 'hostname',
                'port': 'portnamber',
                'user': 'username',
                'pass': 'password'}'''
    conn_params = {'host': params.get('host', '192.168.88.1'),
                   'port': params.get('port', 8728),
                   'user': params.get('user', 'admin'),
                   'pass': params.get('pass', '')}
    
    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    # connect to the router
    # TODO: error handling for connection
    sock.connect((conn_params['host'], conn_params['port']))
    return sock
    # 2. login
    # login(sock, conn_params['user'], conn_params['pass'])

def login(sock, user, password):
    '''Login to the router'''
    # talk to the router with login information
    for replay, attrs in talk(sock, "/login", '=name=' + user, '=password=' + password):
        if replay == '!trap':
            # TODO: Error handling for auth
            print(replay, attrs)
        if 'ret' in attrs:
            # RouterOs pre-v6.43
            for replay2, attrs2 in talk(sock, "/login", "=name=" + user,
                    "=response=00" + auth_response(password, attrs['ret'])):
                if replay2 == '!trap':
                    # TODO: Error handling for auth
                    print(replay2, attrs2)

def auth_response(pwd, ret):
    chal = binascii.unhexlify(ret.encode(sys.stdout.encoding))
    md = hashlib.md5()
    md.update(b'\x00')
    md.update(pwd.encode(sys.stdout.encoding))
    md.update(chal)
    return binascii.hexlify(md.digest()).decode(sys.stdout.encoding)

def talk(sock, command, *params):
    '''Send sentence to the router and read response'''
    response = []
    write_sentence(sock, command, *params)
    # while first world != '!done'
    while True:
        sentence = read_sentence(sock)
        attrs = {}
        for n in range(1, len(sentence)):
            attr = sentence[n].split('=')[1:]
            attrs.update({attr[0]: attr[1]})
        response.append((sentence[0], attrs))
        if sentence[0] == '!done':
            return response

def write_sentence(sock, *worlds):
    '''Send sentence to the router'''
    worlds = list(worlds)
    worlds.append('')
    sentence = bytes()
    for world in worlds:
        sentence += encode_world(world)
    write_bytes(sock, sentence)

def write_bytes(sock, bytes_to_write):
    '''Write bytes to the router'''
    # TODO: rewrite with send
    sock.sendall(bytes_to_write)

def encode_world(world):
    '''Write world to the router'''
    # Get encoded length
    enc_len = encode_len(len(world))
    return enc_len + world.encode('latin1')

def encode_len(length):
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

def read_sentence(sock):
    '''Read sentence'''
    worlds = []
    while True:
        world = read_world(sock)
        if len(world) == 0:
            break
        worlds.append(world)
    return(worlds)

def read_world(sock):
    length = decode_length(sock)
    world = read_bytes(sock, length)
    return world.decode('latin1')

def decode_length(sock):
    def decode_low_bytes(len_, lower_bytes):
        for byte in low_bytes:
            len_ <<= 8
            len_ += byte
        return len_

    len_ = ord(read_bytes(sock, 1))
    if (len_ & 0x80) == 0x00:
        return len_
    elif(len_ & 0xC0) == 0x80:
        len_ &= ~0xC0
        low_bytes = read_bytes(sock, 1)
        return decode_low_bytes(len_, low_bytes)
    elif(len_ & 0xE0) == 0xC0:
        len_ &= ~0xE0
        low_bytes = read_bytes(sock, 2)
        return decode_low_bytes(len_, low_bytes)
    elif(len_ & 0xF0) == 0xE0:
        len_ &= ~0xF0
        low_bytes = read_bytes(sock, 3)
        return decode_low_bytes(len_, low_bytes)
    elif(len_ & 0xF8) == 0xF0:
        low_bytes = read_bytes(sock, 4)
        return decode_low_bytes(0, low_bytes)
    else:
        # Can't be decoded
        # TODO: generate extension
        pass

def read_bytes(sock, n):
    '''Read n bytes from socket'''
    result = bytes()
    while len(result) < n:
       data = sock.recv(n - len(result))
       if data == b'':
           # Connection closed?
           pass
       result += data
    return result
        
if __name__ == '__main__':
    params = {'host': '192.168.166.254',
              'user': 'api',
              'pass': 'test_api'}
    sock = connect(**params)
    login(sock, params['user'], params['pass'])
    response = talk(sock, '/interface/print')
    for sentence in response:
        print(sentence)
    sock.close()
