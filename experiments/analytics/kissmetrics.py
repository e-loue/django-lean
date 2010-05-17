from django_kissmetrics.middleware import TrackingMiddleware

from experiments.analytics import IdentificationError
from experiments.analytics.base import BaseAnalytics


class KissMetrics(BaseAnalytics):
    def __init__(self, KM=None, middleware=None):
        if middleware is None:
            self.middleware = TrackingMiddleware()
        if KM is None:
            KM = self.middleware.KM
        self.KM = KM

    def _id_from_session(self, session):
        id_from_session = self.middleware.id_from_session
        try:
            return id_from_session(session)
        except AttributeError, e:
            raise IdentificationError(e)

    def _id_from_user(self, user):
        id_from_user = self.middleware.id_from_user
        try:
            return id_from_user(user)
        except AttributeError, e:
            raise IdentificationError(e)

    def _identify(self, experiment_user):
        try:
            self.KM.identify(self._compute_id(experiment_user))
            return True
        except IdentificationError:
            # Ignore experiment_users who cannot be tied to sessions or users
            return False

    def _submit(self, name, properties, experiment_user=None):
        if self._identify(experiment_user):
            self.KM.record(action=name, props=properties)
