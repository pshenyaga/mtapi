import argparse
import getpass
import asyncio
from mtapi import asyncapi
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


def login(api):
    '''Try to login to router with max attempts, allowed by router'''
    while True:
        login = input("Login: ")
        password = getpass.getpass()
        try:
            api.loop.run_until_complete(api.login(login, password))
        except mt_error.TrapError as e:
            print(e)
        except mt_error.FatalError:
            raise
        else:
            return


def console(api: asyncapi.API) -> None:
    '''Main console'''
    while True:
        args = input("<<< ").strip().split()
        command = args.pop(0) if len(args) > 0 else ""
        response = api.loop.run_until_complete(api.talk(command, *args))
        for res in response:
            print(">>> ", res[0], res[1])


def main(api: asyncapi.API, address: str, port: str) -> None:
    try:
        api.loop.run_until_complete(api.connect(address, port))
    except:
        raise
    else:
        try:
            login(api)
        except mt_error.FatalError:
            print("Could not login. Connection closed")
        except:
            raise
        else:
            console(api)
    finally:
        api.loop.run_until_complete(api.close())


if __name__ == "__main__":
    address, port = parse_args()
    loop = asyncio.get_event_loop()
    api = asyncapi.API(loop)

    try:
        main(api, address, port)
    except KeyboardInterrupt:
        print("\nGoodbye!")
