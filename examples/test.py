# examples/test.py

from mtapi import hlapi
from mtapi import error as mt_error
import asyncio

if __name__ == '__main__':
    params = {
        'host': '10.253.12.129',
        'port': '8728',
        'user': 'api',
        'pass': 'api_hard_pass'
    }
    
    loop = asyncio.get_event_loop()
    api = hlapi.HlAPI(loop)
    api.set_debug(True)

    async def test():
        try:
            await asyncio.wait_for(api.connect(**params), timeout=5)
        except mt_error.FatalError as e:
            print("Connection closed.")
        except mt_error.TrapError as e:
            print(e)
        except asyncio.futures.TimeoutError:
            print("Time out.")
        except OSError as e:
            print(e)
        else:
            try:
                result = await asyncio.wait_for(api.talk(
                    '/ip/firewall/address-list/print', '?list=ADM-HOSTS'),
                    timeout = 5)
                
            except mt_error.FatalError as e:
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
