from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core import mail
from django.db import transaction

from django_lean.lean_retention.models import (DailyActivity, LastActivity,
                                               SignIn)
from django_lean.lean_retention import signals
from django_lean.utils import get_current_site


class BaseTrackingMiddleware(object):
    def _track(self, request, response):
        raise NotImplementedError()
        
    def medium(self, request, response):
        return 'Default'

    def process_response(self, request, response):
        if transaction.is_managed() and not hasattr(mail, 'outbox'):
            # We must ignore this assertion when running inside a
            # Django test case, which uses transactions.
            raise ImproperlyConfigured('%s cannot be inside a transaction.' %
                                       self.__class__.__name__)
        if response.status_code != 200:
            # Ignore failures, as they aren't real activity.
            return response
        if request.is_ajax():
            # Ignore AJAX calls.
            return response
        if request.user.is_anonymous():
            # Ignore anonymous users.
            return response
        return self._track(request=request, response=response)


class TrackRetentionMiddleware(BaseTrackingMiddleware):
    """
    Tracks which days a user has used the application.

    To use, install in settings.MIDDLEWARE_CLASSES before
    `TransactionMiddleware`, to prevent failures due to multiple
    requests racing to update `DailyActivity` objects.

    MIDDLEWARE_CLASSES = (
        'django_lean.lean_retention.middleware.TrackRetentionMiddleware',
        'django.middleware.transaction.TransactionMiddleware',
    )
    """
    def _track(self, request, response):
        # Has the user done anything today?
        activity, created = DailyActivity.objects.stamp(
            user=request.user, site=get_current_site(),
            medium=self.medium(request=request, response=response)
        )
        if created:
            # Send a signal as the user has become active today
            signals.new_day.send(daily_activity=activity,
                                 request=request, sender=self.__class__)
        return response


class TrackSigninMiddleware(BaseTrackingMiddleware):
    """
    Tracks when users have last signed in.

    To use, install in settings.MIDDLEWARE_CLASSES before
    `TransactionMiddleware`, to prevent failures due to multiple
    requests racing to update `LastActivity` objects.

    MIDDLEWARE_CLASSES = (
        'django_lean.lean_retention.middleware.TrackSigninMiddleware',
        'django.middleware.transaction.TransactionMiddleware',
    )
    """
    def _track(self, request, response):
        # Figure out when the user last had any activity
        user = request.user
        now = datetime.now()
        site = get_current_site()
        medium = self.medium(request=request, response=response)
        activity, created = LastActivity.objects.get_or_create(
            user=user, site=site, medium=medium, defaults={'datetime': now}
        )
        past = activity.datetime
        if (now - past) > timedelta(seconds=1):
            # Update the last activity stamp
            activity.datetime = now
            activity.save()
        if created or \
           (now - past) > timedelta(seconds=settings.LAST_ACTIVITY_WINDOW):
            sign_in = self.create_sign_in(user=user, medium=medium,
                                          datetime=now)
            # Send a signal as the user has become active again
            signals.sign_in.send(sign_in=sign_in, request=request,
                                 sender=self.__class__)
        return response

    def create_sign_in(self, user, medium, datetime):
        """Log the fact that the user has become active again."""
        sign_in, _ = SignIn.objects.get_or_create(site=get_current_site(),
                                                  user=user, medium=medium,
                                                  datetime=datetime)
        return sign_in
