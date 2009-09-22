import logging
l = logging.getLogger(__name__)

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase

from experiments.loader import ExperimentLoader
from experiments.models import Experiment, Participant


def create_user_in_group(experiment, i, group, enrollment_date):
    user = User(username="user%s_%s" % (i, group),
                email="email%s_%s@example.com" % (i, group))
    user.save()
    experiment_participant = Participant(user=user,
                                         experiment=experiment,
                                         group=group)
    experiment_participant.save()
    experiment_participant.enrollment_date = enrollment_date
    experiment_participant.save()
    return user

class TestCase(DjangoTestCase):
    def _pre_setup(self):
        super(TestCase, self)._pre_setup()
        experiments = getattr(self, 'experiments', [])
        ExperimentLoader.load_all_experiments(apps=experiments)


class TestUser(object):
    """
    A utility class for testing that implements an 'ExperimentUser' object
    useful in tests.
    """

    def __init__(self, username=None, anonymous_visitor=None,
                 verified_human=True):
        if anonymous_visitor:
            self.anonymous_id = anonymous_visitor.id
        else:
            self.anonymous_id = None

        if not username == None:
            self.user, created = User.objects.get_or_create(
                username=username, email="%s@example.com" % username)
        else:
            self.user = None

        self.verified_human = verified_human
        self.temporary_enrollments = {}

    def is_anonymous(self):
        return self.user == None

    def set_anonymous_id(self, anonymous_id):
        self.anonymous_id = anonymous_id

    def get_anonymous_id(self):
        return self.anonymous_id

    def get_registered_user(self):
        return self.user

    def is_verified_human(self):
        return self.verified_human

    def store_temporary_enrollment(self, experiment_name, group_id):
        self.temporary_enrollments[experiment_name] = group_id

    def get_added_enrollments(self):
        return self.temporary_enrollments

    def get_temporary_enrollment(self, experiment_name):
        added_enrollments = self.get_added_enrollments()
        if not added_enrollments:
            return None
        else:
            return added_enrollments.get(experiment_name)
