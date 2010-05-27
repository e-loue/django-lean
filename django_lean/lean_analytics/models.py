from django_lean.experiments.models import GoalRecord
from django_lean.experiments.signals import goal_recorded, user_enrolled
from django_lean.lean_analytics import get_all_analytics


def analytics_goalrecord(sender, goal_record, experiment_user, *args, **kwargs):
    for analytics in get_all_analytics():
        analytics.record(goal_record=goal_record,
                         experiment_user=experiment_user)

goal_recorded.connect(analytics_goalrecord, sender=GoalRecord)

def analytics_enrolled(sender, experiment, experiment_user, group_id,
                       *args, **kwargs):
    for analytics in get_all_analytics():
        analytics.enroll(experiment=experiment,
                         experiment_user=experiment_user,
                         group_id=group_id)

user_enrolled.connect(analytics_enrolled)
