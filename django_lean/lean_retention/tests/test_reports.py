from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

import mox

from django_lean.lean_retention.models import DailyActivity
from django_lean.lean_retention.reports import (sort_retention_periods,
                                                Cohort, Period)
from django_lean.utils import get_current_site


class TestReportUtils(TestCase):
    def test_sort_retention_periods(self):
        self.assertEqual(sort_retention_periods([]), [])
        self.assertEqual(sort_retention_periods([1, 2, 3]), [1, 2, 3])
        self.assertEqual(sort_retention_periods([1, 1, 1]), [1])
        self.assertEqual(sort_retention_periods([1, 2, 1]), [1, 2])
        self.assertRaises(TypeError, sort_retention_periods, ['1', '2', '3'])
        self.assertRaises(TypeError, sort_retention_periods, ['1', 2, 3])
        self.assertRaises(ValueError, sort_retention_periods, [0, 1, 2])
        self.assertRaises(ValueError, sort_retention_periods, [-1, 1, 2])


class TestPeriod(TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.user = User.objects.create_user('user', 'user@example.com', 'user')
        self.activity, _ = DailyActivity.objects.stamp(user=self.user,
                                                       site=get_current_site(),
                                                       medium='Default')
        self.activity.days = 29
        self.activity.save()

    def test_create(self):
        self.assertRaises(ValueError, Period,
                          cohort=None, start_day=1, end_day=1)
        self.assertRaises(ValueError, Period,
                          cohort=None, start_day=30, end_day=1)
        
    def test_length(self):
        period = Period(cohort=None, start_day=1, end_day=30)
        self.assertEqual(period.length(), 29)

    def test_activities(self):
        cohort = self.mox.CreateMockAnything()
        cohort.users = User.objects.all()
        self.mox.ReplayAll()
        self.assertEqual(
            list(Period(cohort, start_day=1, end_day=30).activities),
            [self.activity]
        )
        self.assertEqual(
            list(Period(cohort, start_day=30, end_day=60).activities),
            []
        )
        self.mox.VerifyAll()

    def test_users(self):
        cohort = self.mox.CreateMockAnything()
        cohort.users = User.objects.all()
        self.mox.ReplayAll()
        self.assertEqual(list(Period(cohort, start_day=1, end_day=30).users),
                         [self.user])
        self.assertEqual(list(Period(cohort, start_day=30, end_day=60).users),
                         [])
        self.mox.VerifyAll()

    def test_periods(self):
        cohort = self.mox.CreateMockAnything()
        cohort.users = User.objects.all()
        self.mox.ReplayAll()
        periods = list(Period.periods(cohort, [60, 30, 90]))
        for period in periods:
            self.assertEqual(period.cohort, cohort)
        self.assertEqual(periods[0].start_day, 1)
        self.assertEqual(periods[0].end_day, 30)
        self.assertEqual(periods[1].start_day, 30)
        self.assertEqual(periods[1].end_day, 60)
        self.assertEqual(periods[2].start_day, 60)
        self.assertEqual(periods[2].end_day, 90)
        self.mox.VerifyAll()


class TestCohort(TestCase):
    def setUp(self):
        midnight = time(0, 0, 0)
        yesterday = datetime.combine(date.today() - timedelta(days=1), midnight)
        day_before = datetime.combine(yesterday - timedelta(days=1), midnight)
        self.user1 = User.objects.create_user('user1', 'user1@example.com',
                                              'user1')
        self.user1.date_joined = day_before
        self.user1.save()
        self.user2 = User.objects.create_user('user2', 'user2@example.com',
                                              'user2')
        self.user2.date_joined = yesterday
        self.user2.save()

    def test_create(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        self.assertRaises(ValueError,
                          Cohort, start_date=today, end_date=yesterday,
                          retention_periods=[])
        cohort = Cohort(start_date=yesterday, end_date=today,
                        retention_periods=[2, 1, 3])
        self.assertEqual(cohort.start_date, yesterday)
        self.assertEqual(cohort.end_date, today)
        self.assertEqual(cohort.retention_periods, [1, 2, 3])

    def test_periods(self):
        yesterday = date.today() - timedelta(days=1)
        day_before = yesterday - timedelta(days=1)
        cohort = Cohort(start_date=day_before, end_date=yesterday,
                        retention_periods=[40, 20, 60])
        self.assertEqual(cohort.periods[0].start_day, 1)
        self.assertEqual(cohort.periods[0].end_day, 20)
        self.assertEqual(cohort.periods[1].start_day, 20)
        self.assertEqual(cohort.periods[1].end_day, 40)
        self.assertEqual(cohort.periods[2].start_day, 40)
        self.assertEqual(cohort.periods[2].end_day, 60)

    def test_users(self):
        yesterday = date.today() - timedelta(days=1)
        day_before = yesterday - timedelta(days=1)
        cohort = Cohort(start_date=day_before, end_date=yesterday,
                        retention_periods=[])
        self.assertEqual(set(cohort.users), set([self.user1, self.user2]))
        cohort = Cohort(start_date=yesterday, end_date=yesterday,
                        retention_periods=[])
        self.assertEqual(set(cohort.users), set([self.user2]))

    def test_cohorts(self):
        yesterday = date.today() - timedelta(days=1)
        retention_periods = [1]
        cohorts = Cohort.cohorts(end_date=date.today(), length=2,
                                 retention_periods=retention_periods)
        # First cohort should have both users
        cohort = cohorts.next()
        self.assertEqual(set(cohort.users), set([self.user1, self.user2]))
        self.assertEqual(cohort.start_date, yesterday - timedelta(days=1))
        self.assertEqual(cohort.end_date, yesterday)
        self.assertEqual(cohort.retention_periods, retention_periods)
        # Next cohort should only have user1
        cohort = cohorts.next()
        self.assertEqual(set(cohort.users), set([self.user1]))
        self.assertEqual(cohort.start_date, yesterday - timedelta(days=2))
        self.assertEqual(cohort.end_date, yesterday - timedelta(days=1))
        self.assertEqual(cohort.retention_periods, retention_periods)
        # Next cohort should only have no users
        cohort = cohorts.next()
        self.assertEqual(set(cohort.users), set())
        self.assertEqual(cohort.start_date, yesterday - timedelta(days=3))
        self.assertEqual(cohort.end_date, yesterday - timedelta(days=2))
        self.assertEqual(cohort.retention_periods, retention_periods)
