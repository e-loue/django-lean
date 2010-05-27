from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core import mail
from django.db import transaction

from django_lean.lean_retention.models import LastActivity, SignIn
from django_lean.lean_retention import signals


class TrackSigninMiddleware(object):
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
        user = request.user
        if user.is_anonymous():
            # Anonymous users can't sign in.
            return response
        # Figure out when the user last had any activity
        now = datetime.now()
        medium = self.medium(request, response)
        activity, created = LastActivity.objects.get_or_create(
            user=user, medium=medium, defaults={'datetime': now}
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
        sign_in, _ = SignIn.objects.get_or_create(user=user, medium=medium,
                                                  datetime=datetime)
        return sign_in
