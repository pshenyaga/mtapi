import argparse
import getpass
import os, pwd
from mtapi import blockingdapi
from mtapi import error as mterror

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
    parser.add_argument("-u", "--user",
                        help="username")
    parser.add_argument("-p", "--password",
                        help="password")
    parser.add_argument("-l", "--list",
                        help="list to get")

    args = parser.parse_args()

    return args

def get_address_list(api, list_name):
    '''Get address list from given router. If list_name not defined - returns
    all lists
    Usage:
        address_list = get_address_list(api, list)
    Params:
        api: connected blocked API
        list_name (optional): address list name'''

    args = ()
    command = '/ip/firewall/address-list/print'
    result = []

    if list_name:
        args = ('?list={}'.format(list_name), )

    try:
        result = api.talk(command, *args)
    except:
        raise
    else:
        return result



def main():
    args = parse_args()
    if not args.user:
        args.user = pwd.getpwuid(os.getuid()).pw_name
        args.password = getpass.getpass(
            'Password for user {}: '.format(args.user))

    if not args.password:
        args.password = getpass.getpass(
            'Password for user {}: '.format(args.user))

    # Bad solution. I have to add context manager to blockingapi.
    api = None;
    try:
        api = blockingapi.connect(
            args.address,
            args.port,
            args.user,
            args.password
        )
    except:
        raise
    else:
        address_list = get_address_list(api, args.list)
        for record in address_list:
            if args.list:
                print(record[1]['address'])
            else:
                print(record[1]['list'], record[1]['address'])
    finally:
        if api:
            api.close()


if __name__ == '__main__':

    main()
