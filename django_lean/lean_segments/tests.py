from __future__ import with_statement

from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from django_lean.lean_segments.models import Segment
from django_lean.lean_segments.utils import get_segments
from django_lean.utils import patch


NEW_USER_SEGMENTS = [
    ('new', 'New User'),
    ('existing', 'Existing User'),
]


class NewUserSegment(Segment):
    SEGMENTS = NEW_USER_SEGMENTS

    @classmethod
    def get_segment(cls, user, date):
        if user.date_joined.date() == date:
            # New users signed up on `date`
            return 'new'
        return 'existing'


class TestSegment(TestCase):
    S = Segment
    
    def test_metaclass(self):
        self.assertEqual(self.S.SEGMENTS, [])
        self.assertEqual(self.S._meta.get_field('segment').choices, [])
        self.assertEqual([(k, l) for k, l in self.S._segments.items()], [])

    def test_keys(self):
        self.assertEqual(list(self.S.keys()), [])

    def test_label(self):
        self.assertRaises(KeyError, self.S.label, 'invalid')

    def test_get_segment(self):
        self.assertRaises(NotImplementedError,
                          self.S.get_segment, user=None, date=None)


class TestNewUserSegment(TestCase):
    S = NewUserSegment

    def setUp(self):
        self.today = User.objects.create_user('today', 'today@example.com',
                                              'today')
        self.new = User.objects.create_user('new', 'new@example.com', 'new')
        self.new.date_joined = datetime.now() - timedelta(days=1)
        self.new.save()
        self.existing = User.objects.create_user('existing',
                                                 'existing@example.com',
                                                 'existing')
        self.existing.date_joined = datetime.now() - timedelta(days=2)
        self.existing.save()
    
    def test_metaclass(self):
        self.assertEqual(self.S.SEGMENTS, NEW_USER_SEGMENTS)
        self.assertEqual(self.S._meta.get_field('segment').choices,
                         NEW_USER_SEGMENTS)
        self.assertEqual([(k, l) for k, l in self.S._segments.items()],
                         NEW_USER_SEGMENTS)

    def test_keys(self):
        self.assertEqual(list(self.S.keys()),
                         [k for k, l in NEW_USER_SEGMENTS])

    def test_label(self):
        self.assertRaises(KeyError, self.S.label, 'invalid')
        self.assertEqual(self.S.label('new'), 'New User')

    def test_assign_today(self):
        results = self.S.objects.assign(user=self.today)
        self.assertEqual(results, [])

    def test_assign_new(self):
        results = self.S.objects.assign(user=self.new)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user, self.new)
        self.assertEqual(results[0].date, date.today() - timedelta(days=1))
        self.assertEqual(results[0].segment, 'new')

    def test_assign_existing(self):
        results = self.S.objects.assign(user=self.existing)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].user, self.existing)
        self.assertEqual(results[0].date, date.today() - timedelta(days=1))
        self.assertEqual(results[0].segment, 'existing')
        self.assertEqual(results[1].user, self.existing)
        self.assertEqual(results[1].date, date.today() - timedelta(days=2))
        self.assertEqual(results[1].segment, 'new')

    def test_missing_dates(self):
        # All dates should be missing
        self.assertEqual(self.S.objects.missing_dates(user=self.existing),
                         [date.today() - timedelta(days=2),
                          date.today() - timedelta(days=1)])
        # No dates should be missing
        results = self.S.objects.assign(user=self.existing)
        self.assertEqual(self.S.objects.missing_dates(user=self.existing), [])
        # Deleted date should be missing
        results[-1].delete()
        self.assertEqual(self.S.objects.missing_dates(user=self.existing),
                         [date.today() - timedelta(days=2)])


class TestUtils(TestCase):
    def test_get_segments(self):
        segment_name = '%s.%s' % (self.__module__, NewUserSegment.__name__)
        with patch(settings, 'LEAN_SEGMENTS', [segment_name]):
            self.assertEqual(settings.LEAN_SEGMENTS, [segment_name])
            self.assertEqual(get_segments(), [NewUserSegment])
