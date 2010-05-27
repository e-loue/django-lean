from datetime import datetime, timedelta
from time import sleep

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from django_lean.lean_retention.models import LastActivity, SignIn
from django_lean.lean_retention.tests.utils import TestCase


class TestTrackSigninMiddleware(TestCase):
    middleware = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django_lean.lean_retention.middleware.TrackSigninMiddleware',
        'django.middleware.transaction.TransactionMiddleware',
    ]
    urls = 'django_lean.lean_retention.tests.urls'
    
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@example.com', 'user')
        self.original_window = settings.LAST_ACTIVITY_WINDOW

    def tearDown(self):
        settings.LAST_ACTIVITY_WINDOW = self.original_window

    def test_anonymous(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LastActivity.objects.count(), 0)
        self.assertEqual(SignIn.objects.count(), 0)

    def assertActivity(self, activity, user, medium, datetime):
        self.assertEqual(activity.user, user)
        self.assertEqual(activity.medium, medium)
        self.assertTrue(activity.datetime - datetime < timedelta(seconds=1),
                        '%r is not close to %r' % (activity.datetime, datetime))

    def test_sign_in(self):
        settings.LAST_ACTIVITY_WINDOW = 0
        # Sign in
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.user.username))
        now = datetime.now()
        # Hit the page
        response = self.client.get(reverse('home'))
        self.assertEqual(LastActivity.objects.count(), 1)
        self.assertActivity(LastActivity.objects.all()[0],
                            user=self.user, medium='Default', datetime=now)
        self.assertEqual(SignIn.objects.count(), 1)
        self.assertActivity(SignIn.objects.order_by('-id')[0],
                            user=self.user, medium='Default', datetime=now)
        # Hit the page again within the time limit
        response = self.client.get(reverse('home'))
        self.assertEqual(LastActivity.objects.count(), 1)
        self.assertActivity(LastActivity.objects.all()[0],
                            user=self.user, medium='Default', datetime=now)
        self.assertEqual(SignIn.objects.count(), 1)
        self.assertActivity(SignIn.objects.order_by('-id')[0],
                            user=self.user, medium='Default', datetime=now)

    def test_return(self):
        settings.LAST_ACTIVITY_WINDOW = 1
        # Sign in
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.user.username))
        now = datetime.now()
        # Hit the page
        response = self.client.get(reverse('home'))
        self.assertEqual(LastActivity.objects.count(), 1)
        self.assertActivity(LastActivity.objects.all()[0],
                            user=self.user, medium='Default', datetime=now)
        self.assertEqual(SignIn.objects.count(), 1)
        self.assertActivity(SignIn.objects.order_by('-id')[0],
                            user=self.user, medium='Default', datetime=now)
        # Hit the page again within the time limit
        sleep(2)
        now = datetime.now()
        response = self.client.get(reverse('home'))
        self.assertEqual(LastActivity.objects.count(), 1)
        self.assertActivity(LastActivity.objects.all()[0],
                            user=self.user, medium='Default', datetime=now)
        self.assertEqual(SignIn.objects.count(), 2)
        self.assertActivity(SignIn.objects.order_by('-id')[0],
                            user=self.user, medium='Default', datetime=now)
