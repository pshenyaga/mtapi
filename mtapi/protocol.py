# protocol.py

import sys

class Protocol:
    def __init__(self, reader, writer):
        self.writer = writer
        self.reader = reader

# Writer
    def write_sentence(self, *words):
        '''Send sentence to the router'''
        words = list(words)
        words.append('')
        sentence = bytes()

        for word in words:
            sentence += self._encode_word(word)
        self.writer.write(sentence)

    def _encode_word(self, word):
        '''Encode word'''
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

# Reader
    async def read_sentence(self):
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
        word = await self.reader.readexactly(len_)
        return word.decode('latin1')

    async def _read_length(self):
        def decode_low_bytes(len_, lower_bytes):
            for byte in low_bytes:
                len_ <<= 8
                len_ += byte
            return len_

        len_ = ord(await self.reader.readexactly(1))
        if (len_ & 0x80) == 0x00:
            pass
        elif(len_ & 0xC0) == 0x80:
            len_ &= ~0xC0
            low_bytes = await self.reader.readexactly(1)
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xE0) == 0xC0:
            len_ &= ~0xE0
            low_bytes = await self.reader.readexactly(2)
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xF0) == 0xE0:
            len_ &= ~0xF0
            low_bytes = await self.reader.readexactly(3)
            len_ = decode_low_bytes(len_, low_bytes)
        elif(len_ & 0xF8) == 0xF0:
            low_bytes = await self.reader.readexactly(4)
            len_ = decode_low_bytes(0, low_bytes)
        else:
            # Can't be decoded
            # TODO: raise extension
            pass

        return len_

