import datetime

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
    medium = models.CharField(max_length=255, verbose_name=_('medium'),
                              help_text=_('Source of the activity.'))

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%r medium='%s'" % (self.user, self.medium)


class DateTimeActivity(BaseActivity):
    datetime = models.DateTimeField(verbose_name=_('date-time'),
                                    help_text=_('Timestamp of activity'))

    class Meta:
        abstract = True

    def __unicode__(self):
        return ("%s datetime='%s'" %
                (super(DateTimeActivity, self).__unicode__(),
                 self.datetime))


class DailyActivityManager(models.Manager):
    def stamp(self, user, site, medium, date=None):
        if date is None:
            date = datetime.date.today()
        days = self.model.days_since_signup(user=user, date=date)
        return self.get_or_create(user=user, site=site, medium=medium,
                                  date=date, defaults={'days': days})


class DailyActivity(BaseActivity):
    date = models.DateField(verbose_name=_('date'), db_index=True,
                            help_text=_('Date of activity'))
    days = models.PositiveIntegerField(verbose_name=_('day of life'),
                                       db_index=True,
                                       help_text=_('Days since sign up.'),)

    objects = DailyActivityManager()

    def __unicode__(self):
        return "%s date='%s'" % (super(DailyActivity, self).__unicode__(),
                                 self.date)

    @classmethod
    def days_since_signup(cls, user, date):
        return (date - user.date_joined.date()).days



class LastActivity(DateTimeActivity):
    class Meta:
        unique_together = ['user', 'site', 'medium']


class SignIn(DateTimeActivity):
    pass
