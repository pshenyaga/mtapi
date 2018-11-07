# mtapi.py

def connect():
    '''Connect to the router'''
    # 1. create socket and connect
    # 2. login
    login()

def login():
    '''Login to the router'''
    # talk to the router with login information
    talk()
    # check router's response

def talk():
    '''Send sentence to the router and read response'''
    send_sentence()
    read_sentences()

def send_sentences():
    '''Send sentence to the router'''
    pass

def read_sentences():
    '''Read sentences from the router'''
    pass
