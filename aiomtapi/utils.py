import sys
from typing import Optional


def encode_word(word: str):
    '''Encode word'''
    enc_len = encode_len(len(word))

    return enc_len + word.encode('latin1')


def encode_len(length: int) -> bytes:
    '''Encode length'''
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

# def read_word(data: bytes):
#     length, data = decode_length(data)
#     return word.decode('latin1')


# def read_sentence(data: bytes):
#     '''Read sentence'''
#     words = []
#     while True:
#         length, data = decode_length(data)
#         if len(data[:length]) == 0:
#             break
#         words.append((data[:length]).decode('utf-8'))
#         data = data[length:]
#     return words


def decode_lower_bytes(length: int, lower_bytes: bytes) -> int:
    for byte in lower_bytes:
        length <<= 8
        length += byte
    return length


def decode_length(data: bytes) -> Optional[int]:
    length = ord(data[:1])
    if (length & 0x80) == 0x00:
        pass
    elif (length & 0xC0) == 0x80:
        lower = data[1:3]
        if len(lower) < 1:
            return None
        length &= ~0xC0
        length = decode_lower_bytes(length, lower)
    elif(length & 0xE0) == 0xC0:
        lower = data[1:4]
        if len(lower) < 2:
            return None
        length &= ~0xE0
        length = decode_lower_bytes(length, lower)
    elif(length & 0xF0) == 0xE0:
        lower = data[1:5]
        if len(lower) < 3:
            return None
        length &= ~0xF0
        length = decode_lower_bytes(length, lower)
    elif(length & 0xF8) == 0xF0:
        lower = data[1:6]
        if len(lower) < 4:
            return None
        length = decode_lower_bytes(0, lower)
    else:
        # Can't be decoded
        # TODO: raise extension
        pass
    return length
