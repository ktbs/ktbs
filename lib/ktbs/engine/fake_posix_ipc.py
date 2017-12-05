"""
I provide a dummy implementation of posix_ipc.

This is used in Windows, who does not hace posix_ipc.
Obviously, this should only be used in mono-thread applications.
"""

SEMAPHORE_VALUE_SUPPORTED = False
O_CREAT = None

class Semaphore(object):

    name = "Semaphore.name"

    def __init__(self, *args, **kw):
        pass

    def acquire(self, timeout=None):
        pass

    def release(self):
        pass

    def close(self):
        pass

    def unlink(self):
        pass

class BusyError(Exception):
    pass
