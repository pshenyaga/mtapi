import unittest
import asyncio

from aiomtapi.protocol import Protocol


class TestProtocol(unittest.IsolatedAsyncioTestCase):
    async def test_connection(self):
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_connection(
            lambda: Protocol(),
            '10.253.127.18', 8728
        )

        try:
            res = await protocol.talk('Hello there!')
            self.assertEqual(6, res)
        finally:
            transport.close()


if __name__ == '__main__':
    unittest.main()
