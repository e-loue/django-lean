from copy import copy

from django.conf import settings
from django.core.urlresolvers import get_callable


def irange(start, end, step):
    current = copy(start)
    while current < end:
        yield current
        current += step

def get_segments():
    return [get_callable(s) for s in settings.LEAN_SEGMENTS]
