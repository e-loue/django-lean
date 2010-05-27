from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_lean.utils import get_current_site


class BaseActivity(models.Model):
    user = models.ForeignKey(User, verbose_name=_('user'))
    site = models.ForeignKey(Site, verbose_name=_('site'),
                             blank=True, null=True,
                             default=get_current_site)
    datetime = models.DateTimeField()
    medium = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%r datetime='%s' medium='%s'" % (self.user,
                                                 self.datetime,
                                                 self.medium)


class LastActivity(BaseActivity):
    class Meta:
        unique_together = ['user', 'site', 'medium']


class SignIn(BaseActivity):
    pass
