from datetime import date, timedelta
import warnings

try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import ugettext_lazy as _

from django_lean.lean_segments.utils import irange
from django_lean.utils import get_current_site, in_transaction


ONE_DAY = timedelta(days=1)


class SegmentBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        result = super(SegmentBase, cls).__new__(cls, name, bases, attrs)
        # Configure the `segments` field.
        segments = result.SEGMENTS
        result._segments = OrderedDict(segments)
        segment_field = result._meta.get_field('segment')
        segment_field._choices = segments
        result.__newcls__()
        return result


class SegmentManager(models.Manager):
    def assign(self, user, site=None, start_date=None, end_date=None):
        if site is None:
            site = get_current_site()
        result = []
        for date in reversed(self.missing_dates(user=user, site=site,
                                                start_date=start_date,
                                                end_date=end_date)):
            user_segment, created = self.get_or_create(
                user=user, site=site, date=date
            )
            if not user_segment.segment:
                try:
                    user_segment.segment = self.model._get_segment(user=user,
                                                                   date=date)
                    if not user_segment.segment:
                        raise ValueError('get_segment cannot be empty: %r' %
                                         user_segment.segment)
                except:
                    user_segment.delete()
                    raise
                user_segment.save()
            result.append(user_segment)
        return result

    def missing_dates(self, user, site=None, start_date=None, end_date=None):
        if site is None:
            site = get_current_site()
        date_joined = user.date_joined.date()
        if start_date is None or start_date < date_joined:
            # Start looking from the day the user joined.
            start_date = date_joined
        today = date.today()
        if end_date is None or end_date >= today:
            # Stop looking at yesterday, because today is not valid.
            end_date = today - ONE_DAY
        # Figure out which dates have already been computed
        segments = self.model.objects.filter(user=user, site=site)
        if site is None:
            segments = segments.filter(site__isnull=True)
        dates = segments.filter(date__range=(start_date, end_date)).values_list(
            'date', flat=True
        )
        # Figure out the missing dates
        date_range = irange(start_date, end_date + ONE_DAY, ONE_DAY)
        return list(sorted(set(date_range) - set(dates)))


class Segment(models.Model):
    user = models.ForeignKey(User, verbose_name=_('user'))
    site = models.ForeignKey(Site, verbose_name=_('site'),
                             blank=True, null=True,
                             default=get_current_site)
    date = models.DateField(verbose_name=_('date'), db_index=True)
    segment = models.CharField(max_length=255, verbose_name=_('segment'),
                               db_index=True)

    objects = SegmentManager()

    SEGMENTS = [
        # ('key': 'Human readable label'),
    ]

    __metaclass__ = SegmentBase

    class Meta:
        unique_together = [('user', 'site', 'date')]
        abstract = True

    def __unicode__(self):
        return ("user=%r date='%s' segment=%r" %
                (self.user, self.date, self.segment))

    @classmethod
    def __newcls__(cls):
        pass

    @classmethod
    def get_segment(cls, user, date):
        raise NotImplementedError()

    @classmethod
    def _get_segment(cls, user, date):
        if in_transaction():
            warnings.warn('Inside a transaction: may cause performance issues.',
                          RuntimeWarning, stacklevel=3)
        return cls.get_segment(user, date)

    @classmethod
    def keys(cls):
        return cls._segments.iterkeys()

    @classmethod
    def label(cls, key):
        return cls._segments[key]
