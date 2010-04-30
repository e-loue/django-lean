class BaseAnalytics(object):
    def enroll(self, experiment, experiment_user, group_id):
        raise NotImplementedError()

    def record(self, goal_record, experiment_user):
        raise NotImplementedError()
