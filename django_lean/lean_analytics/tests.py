from __future__ import with_statement

from contextlib import contextmanager

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpRequest

from django_lean.experiments.models import (AnonymousVisitor, Experiment,
                                            GoalRecord, GoalType, Participant)
from django_lean.experiments.tests.utils import get_session, patch, TestCase
from django_lean.experiments.utils import StaticUser, WebUser
from django_lean.lean_analytics import (get_all_analytics,
                                        get_all_analytics_names,
                                        reset_caches,
                                        IdentificationError)
from django_lean.lean_analytics.base import BaseAnalytics

import mox

class TestAnalytics(TestCase):
    def test_get_all_analytics_names(self):
        with patch(settings, 'LEAN_ANALYTICS', NotImplemented):
            reset_caches()
            self.assertEqual(get_all_analytics_names(), ())
        with patch(settings, 'LEAN_ANALYTICS', []):
            reset_caches()
            self.assertEqual(get_all_analytics_names(), [])
        base_name = '%s.%s' % (BaseAnalytics.__module__, BaseAnalytics.__name__)
        with patch(settings, 'LEAN_ANALYTICS', [base_name]):
            reset_caches()
            self.assertEqual(get_all_analytics_names(), [base_name])

    def test_get_all_analytics(self):
        with patch(settings, 'LEAN_ANALYTICS', NotImplemented):
            reset_caches()
            self.assertEqual(get_all_analytics(), [])
        with patch(settings, 'LEAN_ANALYTICS', []):
            reset_caches()
            self.assertEqual(get_all_analytics(), [])
        base_name = '%s.%s' % (BaseAnalytics.__module__, BaseAnalytics.__name__)
        with patch(settings, 'LEAN_ANALYTICS', [base_name]):
            reset_caches()
            self.assertEqual([a.__class__.__name__ for a in get_all_analytics()],
                             [BaseAnalytics.__name__])


#############
# KISSMETRICS
#############

try:
    import django_kissmetrics
except ImportError:
    if 'django_lean.lean_analytics.kissmetrics.KissMetrics' in \
       get_all_analytics_names():
        traceback.print_exc()
else:
    from django_lean.lean_analytics.kissmetrics import KissMetrics


    class TestKissMetrics(TestCase):
        def setUp(self):
            self.mox = mox.Mox()
            self.analytics = KissMetrics()

        def test_id_from_user(self):
            user = User.objects.create_user('user', 'user@example.com', 'user')
            self.assertEqual(self.analytics._id_from_user(user),
                             'User %d' % user.pk)
            self.assertRaises(IdentificationError,
                              self.analytics._id_from_user, None)

        def test_id_from_session(self):
            # With real session
            with self.web_user(AnonymousUser()) as experiment_user:
                self.mox.ReplayAll()
                session = experiment_user.session
                self.assertEqual(
                    self.analytics._id_from_session(experiment_user.session),
                    'Session %s' % session.session_key
                )
                self.mox.VerifyAll()

            # With dict as session
            experiment_user = StaticUser()
            self.assertRaises(IdentificationError,
                              self.analytics._id_from_session,
                              experiment_user.session)

        def test_compute_id(self):
            # With anonymous WebUser
            with self.web_user(AnonymousUser()) as experiment_user:
                session = experiment_user.session
                self.mox.ReplayAll()
                self.assertEqual(self.analytics._compute_id(experiment_user),
                                 'Session %s' % session.session_key)
                self.mox.VerifyAll()

            # With authenticated WebUser
            user = User.objects.create_user('user', 'user@example.com', 'user')
            with self.web_user(user) as experiment_user:
                self.mox.ReplayAll()
                self.assertEqual(self.analytics._compute_id(experiment_user),
                                 'User %d' % user.id)
                self.mox.VerifyAll()

            # With StaticUser
            experiment_user = StaticUser()
            self.assertRaises(IdentificationError,
                              self.analytics._compute_id, experiment_user)

        def test_identify(self):
            # With anonymous WebUser
            with self.web_user(AnonymousUser()) as experiment_user:
                self.mox.ReplayAll()
                self.assertTrue(self.analytics._identify(experiment_user))
                self.mox.VerifyAll()

            # With authenticated WebUser
            user = User.objects.create_user('user', 'user@example.com', 'user')
            with self.web_user(user) as experiment_user:
                self.mox.ReplayAll()
                self.assertTrue(self.analytics._identify(experiment_user))
                self.mox.VerifyAll()

            # With StaticUser
            experiment_user = StaticUser()
            self.assertFalse(self.analytics._identify(experiment_user))

        def test_enroll(self):
            experiment = Experiment.objects.create(name='Experiment')
            user = User.objects.create_user('user', 'user@example.com', 'user')
            KM = self.mox.CreateMockAnything()
            analytics = KissMetrics(KM=KM)
            with self.web_user(user) as experiment_user:
                KM.identify(analytics._compute_id(experiment_user))
                KM.record(action='Enrolled In Experiment',
                          props={'Experiment': experiment.name,
                                 'Group': 'Test'})
                self.mox.ReplayAll()
                analytics.enroll(experiment=experiment,
                                 experiment_user=experiment_user,
                                 group_id=Participant.TEST_GROUP)
                self.mox.VerifyAll()

        def test_record(self):
            KM = self.mox.CreateMockAnything()
            analytics = KissMetrics(KM=KM)
            with self.web_user(AnonymousUser()) as experiment_user:
                KM.identify(analytics._id_from_session(experiment_user.session))
                KM.record(action='Goal Recorded',
                          props={'Goal Type': 'Goal Type'})
                self.mox.ReplayAll()
                goal_type = GoalType.objects.create(name='Goal Type')
                goal_record = GoalRecord.record(goal_name=goal_type.name,
                                                experiment_user=experiment_user)
                analytics.record(goal_record=goal_record,
                                 experiment_user=experiment_user)
                self.mox.VerifyAll()

        def test_event(self):
            KM = self.mox.CreateMockAnything()
            analytics = KissMetrics(KM=KM)
            with self.web_user(AnonymousUser()) as experiment_user:
                KM.identify(analytics._id_from_session(experiment_user.session))
                KM.record(action='Event', props={'Foo': 'Bar'})
                self.mox.ReplayAll()
                analytics.event(name='Event',
                                properties={'Foo': 'Bar'},
                                request=experiment_user.request)
                self.mox.VerifyAll()

        @contextmanager
        def web_user(self, user):
            session = get_session(None)
            request = self.mox.CreateMock(HttpRequest)
            request.user = user
            request.session = session
            experiment_user = WebUser(request)
            experiment_user.get_or_create_anonymous_visitor()
            yield experiment_user


##########
# MIXPANEL
##########

try:
    import mixpanel
except ImportError:
    if 'django_lean.lean_analytics.mixpanel.Mixpanel' in \
       get_all_analytics_names():
        traceback.print_exc()
else:
    from django_lean.lean_analytics.mixpanel import Mixpanel


    class TestMixpanel(TestCase):
        def setUp(self):
            self.mox = mox.Mox()
            self.analytics = Mixpanel()

        def tearDown(self):
            self.mox.UnsetStubs()

        def test_id_from_user(self):
            user = User.objects.create_user('user', 'user@example.com', 'user')
            self.assertEqual(self.analytics._id_from_user(user),
                             'User %d' % user.pk)
            self.assertRaises(IdentificationError,
                              self.analytics._id_from_user, None)

        def test_id_from_session(self):
            # With real session
            with self.web_user(AnonymousUser()) as experiment_user:
                self.mox.ReplayAll()
                session = experiment_user.session
                self.assertEqual(
                    self.analytics._id_from_session(experiment_user.session),
                    'Session %s' % session.session_key
                )
                self.mox.VerifyAll()

            # With dict as session
            experiment_user = StaticUser()
            self.assertRaises(IdentificationError,
                              self.analytics._id_from_session,
                              experiment_user.session)

        def test_compute_id(self):
            # With anonymous WebUser
            with self.web_user(AnonymousUser()) as experiment_user:
                session = experiment_user.session
                self.mox.ReplayAll()
                self.assertEqual(self.analytics._compute_id(experiment_user),
                                 'Session %s' % session.session_key)
                self.mox.VerifyAll()

            # With authenticated WebUser
            user = User.objects.create_user('user', 'user@example.com', 'user')
            with self.web_user(user) as experiment_user:
                self.mox.ReplayAll()
                self.assertEqual(self.analytics._compute_id(experiment_user),
                                 'User %d' % user.id)
                self.mox.VerifyAll()

            # With StaticUser
            experiment_user = StaticUser()
            self.assertRaises(IdentificationError,
                              self.analytics._compute_id, experiment_user)

        def test_identify(self):
            # With anonymous WebUser
            with self.web_user(AnonymousUser()) as experiment_user:
                self.mox.ReplayAll()
                self.assertTrue(self.analytics._identify(experiment_user))
                self.assertEqual(
                    self.analytics.identity,
                    'Session %s' % experiment_user.session.session_key
                )
                self.mox.VerifyAll()

            # With authenticated WebUser
            user = User.objects.create_user('user', 'user@example.com', 'user')
            with self.web_user(user) as experiment_user:
                self.mox.ReplayAll()
                self.assertTrue(self.analytics._identify(experiment_user))
                self.assertEqual(self.analytics.identity,
                                 'User %s' % experiment_user.user.pk)
                self.mox.VerifyAll()

            # With StaticUser
            experiment_user = StaticUser()
            self.assertFalse(self.analytics._identify(experiment_user))
            self.assertEqual(self.analytics.identity, None)

        def test_enroll(self):
            import time
            experiment = Experiment.objects.create(name='Experiment')
            user = User.objects.create_user('user', 'user@example.com', 'user')
            tracker = self.mox.CreateMockAnything()
            analytics = Mixpanel(tracker=tracker)
            now = time.gmtime()
            self.mox.StubOutWithMock(time, 'gmtime')
            time.gmtime().AndReturn(now)
            with self.web_user(user) as experiment_user:
                properties = {'time': '%d' % time.mktime(now),
                              'distinct_id': 'User %d' % user.pk,
                              'Experiment': experiment.name,
                              'Group': 'Test'}
                tracker.run(event_name='Enrolled In Experiment',
                            properties=properties)
                self.mox.ReplayAll()
                analytics.enroll(experiment=experiment,
                                 experiment_user=experiment_user,
                                 group_id=Participant.TEST_GROUP)
                self.mox.VerifyAll()

        def test_record(self):
            import time
            tracker = self.mox.CreateMockAnything()
            analytics = Mixpanel(tracker=tracker)
            now = time.gmtime()
            self.mox.StubOutWithMock(time, 'gmtime')
            time.gmtime().AndReturn(now)
            with self.web_user(AnonymousUser()) as experiment_user:
                properties = {
                    'time': '%d' % time.mktime(now),
                    'distinct_id': ('Session %s' %
                                    experiment_user.session.session_key),
                    'Goal Type': 'Goal Type'
                }
                tracker.run(event_name='Goal Recorded',
                            properties=properties)
                self.mox.ReplayAll()
                goal_type = GoalType.objects.create(name='Goal Type')
                goal_record = GoalRecord.record(goal_name=goal_type.name,
                                                experiment_user=experiment_user)
                analytics.record(goal_record=goal_record,
                                 experiment_user=experiment_user)
                self.mox.VerifyAll()

        def test_event(self):
            import time
            tracker = self.mox.CreateMockAnything()
            analytics = Mixpanel(tracker=tracker)
            now = time.gmtime()
            self.mox.StubOutWithMock(time, 'gmtime')
            time.gmtime().AndReturn(now)
            with self.web_user(AnonymousUser()) as experiment_user:
                properties = {
                    'time': '%d' % time.mktime(now),
                    'distinct_id': ('Session %s' %
                                    experiment_user.session.session_key),
                    'Foo': 'Bar'
                }
                tracker.run(event_name='Event',
                            properties=properties)
                self.mox.ReplayAll()
                analytics.event(name='Event',
                                properties={'Foo': 'Bar'},
                                request=experiment_user.request)
                self.mox.VerifyAll()

        @contextmanager
        def web_user(self, user):
            session = get_session(None)
            request = self.mox.CreateMock(HttpRequest)
            request.user = user
            request.session = session
            experiment_user = WebUser(request)
            experiment_user.get_or_create_anonymous_visitor()
            yield experiment_user
