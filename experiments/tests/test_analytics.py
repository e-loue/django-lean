from __future__ import with_statement

from contextlib import contextmanager

from django.conf import settings
from django.test import TestCase

from experiments.analytics import (get_all_analytics, get_all_analytics_names,
                                   reset_caches)
from experiments.analytics.base import BaseAnalytics
from experiments.tests.utils import get_session, patch

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


try:
    import django_kissmetrics
except ImportError:
    from experiments.analytics import get_all_analytics_names
    if 'experiments.analytics.kissmetrics.KissMetrics' in \
       get_all_analytics_names():
        traceback.print_exc()
else:
    from django.contrib.auth.models import AnonymousUser, User
    from django.http import HttpRequest

    from experiments.analytics import IdentificationError
    from experiments.analytics.kissmetrics import KissMetrics
    from experiments.models import (AnonymousVisitor, Experiment,
                                    GoalRecord, GoalType, Participant)
    from experiments.utils import StaticUser, WebUser


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

        @contextmanager
        def web_user(self, user):
            session = get_session(None)
            request = self.mox.CreateMock(HttpRequest)
            request.user = user
            request.session = session
            experiment_user = WebUser(request)
            experiment_user.get_or_create_anonymous_visitor()
            yield experiment_user
