try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict


class Segment(object):
    def __init__(self, key, label):
        self.key = key
        self.label = label

    def __unicode__(self):
        return "key='%s' label='%s'" % (key, label)


class BaseSegments(object):
    segments = [
        # ('key': 'Human readable label'),
    ]

    def assign(self, user, date):
        raise NotImplementedError

    def __init__(self):
        self._segments = OrderedDict(self.segments)

    @property
    def keys(self):
        return self.segments.iterkeys()

    def segment(self, key):
        return self._segments[key]

    def label(self, key):
        try:
            return self.segments[key]
        except KeyError:
            return key


class NewUserSegments(BaseSegments):
    segments = [
        ('new', 'New User'),
        ('existing', 'Existing User'),
    ]

    def assign(self, user, date):
        if user.date_joined.date() == date:
            # New users signed up on `date`
            return self.segment('new')
        return self.segment('existing')
