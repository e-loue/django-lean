from contextlib import contextmanager
from errno import EACCES, EAGAIN
from fcntl import lockf, LOCK_NB
import os
import socket


def openlock(filename, operation, wait=True):
    """
    Returns a file-like object that gets a fnctl() lock.

    `operation` should be one of LOCK_SH or LOCK_EX for shared or
    exclusive locks.

    If `wait` is False, then openlock() will not block on trying to
    acquire the lock.
    """
    f = os.fdopen(os.open(filename, os.O_RDWR | os.O_CREAT, 0666), "r+")
    if not wait:
        operation |= LOCK_NB
    try:
        lockf(f.fileno(), operation)
    except IOError, err:
        if not wait and err.errno in (EACCES, EAGAIN):
            from django.core.management.base import CommandError
            raise CommandError("Could not acquire lock on '%s' held by %s." %
                               (filename, f.readline().strip()))
        raise
    print >>f, "%s:%d" % (socket.gethostname(), os.getpid())
    f.truncate()
    f.flush()
    return f

@contextmanager
def lockfile(filename, operation, wait=True):
    """
    Returns a context manager with a file-like object that gets a fnctl() lock.

    Automatically closes and removes the lock upon completion.

    `operation` should be one of LOCK_SH or LOCK_EX for shared or
    exclusive locks.

    If `wait` is False, then openlock() will not block on trying to
    acquire the lock.
    """
    path = os.path.abspath(filename)
    f = openlock(filename=filename, operation=operation, wait=wait)
    yield f
    os.unlink(path)
    f.close()
