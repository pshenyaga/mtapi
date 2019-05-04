import argparse
import getpass
import asyncio
from mtapi import hlapi
from mtapi import error as mt_error


def parse_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("address",
                        help="address to connect",
                        nargs='?',
                        default="192.168.88.1")
    parser.add_argument("port",
                        help="port to connect",
                        nargs='?',
                        default='8728')
    args = parser.parse_args()

    return args.address, args.port


async def login(api: hlapi.HlAPI) -> None:
    '''Try to login to router with max attempts, allowed by router'''
    while True:
        login = await api.loop.run_in_executor(None, input, "Login: ")
        password = await api.loop.run_in_executor(None, getpass.getpass)
        try:
            await api.login(login, password)
        except mt_error.TrapError as e:
            print(e)
        except mt_error.FatalError:
            raise
        else:
            return


async def console(api: hlapi.HlAPI) -> None:
    '''Main console'''
    while True:
        command = await api.loop.run_in_executor(
            None, input, "<<< ")
        response = await api.talk(command)
        print(">>> ", response)


async def main(loop, address: str, port: str) -> None:
    api = hlapi.HlAPI(loop)
    try:
        await api.connect(address, port)
    except:
        raise
    else:
        try:
            await login(api)
        except mt_error.FatalError:
            print("Could not login. Connection closed")
        else:
            try:
                await console(api)
            except:
                raise
        finally:
            await api.close()
    finally:
        loop.stop()
    

if __name__ == "__main__":
    address, port = parse_args()
    loop = asyncio.get_event_loop()
    loop.create_task(main(loop,
                          address,
                          port))
    loop.run_forever()
