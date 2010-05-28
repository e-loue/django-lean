from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User

from django_lean.lean_retention.models import DailyActivity


def sort_retention_periods(retention_periods):
    result = list(sorted(set(p + 0 for p in retention_periods)))
    if result and result[0] < 1:
        raise ValueError('retention_periods must be greater than one day,'
                         'not %s' % result[0])
    return result


class Period(object):
    def __init__(self, cohort, start_day, end_day):
        self.cohort = cohort
        self.start_day = start_day
        self.end_day = end_day
        if self.start_day < 1:
            raise ValueError("start day '%s' must be >= 1" % self.start_day)
        if self.start_day >= self.end_day:
            raise ValueError("start day '%s' must be before end day '%s'" %
                             (self.start_day, self.end_day))
        self._activities = None
        self._users = None

    def length(self):
        return self.end_day - self.start_day

    @property
    def activities(self):
        if self._activities is None:
            self._activities = DailyActivity.objects.filter(
                user__in=self.cohort.users,
                days__range=(self.start_day, self.end_day - 1)
            )
        return self._activities

    @property
    def users(self):
        if self._users is None:
            self._users = User.objects.filter(
                id__in=self.activities.values('user')
            )
        return self._users

    @classmethod
    def periods(cls, cohort, retention_periods):
        last = 1
        for period in sort_retention_periods(retention_periods):
            yield cls(cohort=cohort, start_day=last, end_day=period)
            last = period


class Cohort(object):
    def __init__(self, start_date, end_date, retention_periods,
                 period_class=Period):
        if hasattr(start_date, 'date'):
            start_date = start_date.date() # Convert to a datetime.date
        if hasattr(end_date, 'date'):
            end_date = end_date.date()  # Convert to a datetime.date
        self.start_date = start_date
        self.end_date = end_date
        if self.start_date > self.end_date:
            raise ValueError("start date '%s' cannot be after end date '%s'" %
                             (self.start_date, self.end_date))
        self.retention_periods = sort_retention_periods(retention_periods)
        self._Period = Period
        self._periods = None
        self._users = None

    @property
    def periods(self):
        if self._periods is None:
            self._periods = list(
                self._Period.periods(cohort=self,
                                     retention_periods=self.retention_periods)
            )
        return self._periods

    @property
    def users(self):
        if self._users is None:
            start = datetime.combine(self.start_date, time(0, 0, 0))
            end = datetime.combine(self.end_date, time(23, 59, 59))
            self._users = User.objects.filter(date_joined__range=(start, end))
        return self._users

    @classmethod
    def cohorts(cls, end_date, length, retention_periods,
                period_class=Period):
        if hasattr(end_date, 'date'):
            end_date = end_date.date()  # Convert to a datetime.date
        # The end date falls on the last day of the shortest retention period
        retention_periods = sort_retention_periods(retention_periods)
        min_period = retention_periods[0] if retention_periods else 0
        end_date -= timedelta(days=min_period)
        # The start date 
        one_day = timedelta(days=1)
        start_date = end_date - timedelta(days=length) + one_day
        # Generate the stream of cohorts, walking backwards
        try:
            while True:
                yield cls(start_date=start_date, end_date=end_date,
                          retention_periods=retention_periods)
                # Walk backwards
                start_date -= one_day
                end_date -= one_day
        except OverflowError:
            raise StopIteration    # We cannot go further back in time
