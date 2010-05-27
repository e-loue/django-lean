from django.contrib.sites.models import Site


def get_current_site():
    if Site._meta.installed:
        return Site.objects.get_current().id
    return None
