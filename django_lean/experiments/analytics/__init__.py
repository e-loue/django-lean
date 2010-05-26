from django.conf import settings
from django.core.urlresolvers import get_callable


class IdentificationError(RuntimeError):
    pass


def get_all_analytics_names():
    return getattr(settings, 'LEAN_ANALYTICS', ())

def get_all_analytics():
    if get_all_analytics.cache is None:
        names = get_all_analytics_names()
        get_all_analytics.cache = [get_callable(a)() for a in names]
    return get_all_analytics.cache

def reset_caches():
    get_all_analytics.cache = None
reset_caches()
