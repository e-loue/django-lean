from experiments.analytics import IdentificationError


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
        raise NotImplementedError()

    def record(self, goal_record, experiment_user):
        raise NotImplementedError()
