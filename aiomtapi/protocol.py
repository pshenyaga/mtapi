import asyncio
from asyncio.transports import Transport, BaseTransport
from typing import TYPE_CHECKING, Union, cast

from .utils import decode_length, encode_word

if TYPE_CHECKING:
    Q = asyncio.Queue[bytes]
else:
    Q = asyncio.Queue


class Protocol(asyncio.Protocol):
    def __init__(self):
        self._loop = asyncio.get_running_loop()
        self._transport: Union[Transport, None] = None
        self._future: Union[asyncio.Future, None] = None
        self._reader_task: Union[asyncio.Task, None] = None
        self._queue: Q = asyncio.Queue()

    def connection_made(self, transport: BaseTransport) -> None:
        self._transport = cast(Transport, transport)
        self._reader_task = self._loop.create_task(self._reader())

    def data_received(self, data: bytes) -> None:
        self._queue.put_nowait(data)

    def connection_lost(self, exc: Union[Exception, None]) -> None:
        if self._transport:
            self._transport.close()

    async def talk(self, expr: str) -> str:
        future = self._loop.create_future()
        self._future = future
        self._write_sentence(expr)
        return await future
        # return result.decode('utf-8')

    def _write_sentence(self, *words):
        '''Send sentence to the router'''
        assert self._transport, 'No connection'
        words = list(words)
        words.append('')
        sentence = bytes()

        for word in words:
            sentence += encode_word(word)
        self._transport.write(sentence)

    async def _reader(self):
        while True:
            data = await self._queue.get()
            # result = read_sentence(data)
            length = decode_length(data)
            assert self._future, 'Unexpected data received'
            self._future.set_result(length)
