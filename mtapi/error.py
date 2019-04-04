# error.py

class Error(Exception):
    """Base class for exceptions in mtapi module"""
    pass

class FatalError(Error):
    pass

class TrapError(Error):
    pass
