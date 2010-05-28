from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from django_lean.lean_retention.models import DailyActivity
from django_lean.lean_retention.tests.utils import TestCase


class TestTrackRetentionMiddleware(TestCase):
    middleware = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django_lean.lean_retention.middleware.TrackRetentionMiddleware',
        'django.middleware.transaction.TransactionMiddleware',
    ]
    urls = 'django_lean.lean_retention.tests.urls'
    
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'user')

    def test_anonymous(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DailyActivity.objects.count(), 0)

    def test_signup_today(self):
        today = date.today()
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.user.username))
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DailyActivity.objects.count(), 1)
        activity = DailyActivity.objects.all()[0]
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.medium, 'Default')
        self.assertEqual(activity.date, today)
        self.assertEqual(activity.days, 0)

    def test_signup_yesterday(self):
        today = date.today()
        self.user.date_joined = datetime.now() - timedelta(days=1)
        self.user.save()
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.user.username))
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DailyActivity.objects.count(), 1)
        activity = DailyActivity.objects.all()[0]
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.medium, 'Default')
        self.assertEqual(activity.date, today)
        self.assertEqual(activity.days, 1)
