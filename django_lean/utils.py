from django.contrib.sites.models import Site
from django.core import mail
from django.db import transaction


def get_current_site():
    if Site._meta.installed:
        return Site.objects.get_current()
    return None

def in_transaction(test_ignore=True):
    result = transaction.is_managed()
    if test_ignore:
        # Ignore when running inside a Django test case, which uses
        # transactions.
        result = result and not hasattr(mail, 'outbox')
    return result
