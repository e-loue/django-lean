from django_lean.experiments.models import Participant
from django_lean.experiments.utils import WebUser
from django_lean.lean_analytics import IdentificationError


class BaseAnalytics(object):
    def _id_from_session(self, session):
        try:
            return 'Session %s' % session.session_key
        except AttributeError, e:
            raise IdentificationError(e)

    def _id_from_user(self, user):
        try:
            return 'User %d' % user.pk
        except AttributeError, e:
            raise IdentificationError(e)

    def _compute_id(self, experiment_user):
        if not experiment_user.is_anonymous():
            return self._id_from_user(experiment_user.user)
        return self._id_from_session(experiment_user.session)

    def enroll(self, experiment, experiment_user, group_id):
        self._submit(name='Enrolled In Experiment',
                     properties={'Experiment': unicode(experiment),
                                 'Group': dict(Participant.GROUPS)[group_id]},
                     experiment_user=experiment_user)

    def record(self, goal_record, experiment_user):
        self._submit(name='Goal Recorded',
                     properties={'Goal Type': unicode(goal_record.goal_type)},
                     experiment_user=experiment_user)

    def event(self, name, properties, request=None):
        if request:
            self._submit(name, properties, experiment_user=WebUser(request))

    def _submit(self, name, properties, experiment_user=None):
        raise NotImplementedError()
