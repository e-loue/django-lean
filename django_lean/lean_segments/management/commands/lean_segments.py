from __future__ import with_statement

from contextlib import closing
from copy import copy
from datetime import date
from fcntl import LOCK_EX
from itertools import chain
from optparse import (OptionParser, OptionValueError,
                      Option as BaseOption)
from time import strptime

from django.contrib.auth.models import User
from django.core.management.base import CommandError, LabelCommand

from django_lean.lean_segments.utils import get_segments
from django_lean.lockfile import lockfile
from django_lean.utils import get_current_site


LOCKFILE = 'lean_segments.lock'

def check_date(option, opt, value):
    try:
        t = strptime(value, '%Y-%m-%d')
        return date(*t[:3])
    except ValueError:
        raise OptionValueError(
            'option %s: invalid date value: %r' % (opt, value)
        )

class Option(BaseOption):
    TYPES = BaseOption.TYPES + ('date',)
    TYPE_CHECKER = copy(BaseOption.TYPE_CHECKER)

    TYPE_CHECKER['date'] = check_date


make_option = Option

class Command(LabelCommand):
    """manage.py lean_segments"""

    ACTIONS = ('update', 'clear')

    option_list = list(LabelCommand.option_list)
    option_list.extend((
        make_option(
            '--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'
        ),
        make_option(
            '--username', action='append',
            help='Update segments for USERNAMES.'
        ),
        make_option(
            '--start', type='date', metavar='DATE',
            help='Start date for segments. (Format: YYYY-MM-DD)'
        ),
        make_option(
            '--end', type='date', metavar='DATE',
            help='End date for segments. (Format: YYYY-MM-DD)'
        ),
        make_option(
            '--wait', action='store_true', default=False,
            help='Wait for lock.'
        )
    ))

    help = """Manage user segments

  Actions:
    update - update user segments
    clear  - clear user segments
    """

    args = 'action'
    label = 'action'

    def info(self, message, **options):
        self.log(message, 1, options)

    def log(self, message, level, options):
        if int(options.get('verbosity', 1)) >= level:
            print message

    def handle(self, *labels, **options):
        if len(labels) != 1:
            raise CommandError('You must specify an %s.' % self.label)
        action = labels[0]
        if action not in self.ACTIONS:
            raise CommandError('%s "%s" must be one of: %s.' %
                               (self.label.capitalize(),
                                action,
                                ", ".join(self.ACTIONS)))
        return super(Command, self).handle(*labels, **options)

    def handle_label(self, label, **options):
        return getattr(self, 'handle_' + label)(
            segments=get_segments(),
            usernames=options.get('usernames'),
            start_date=options.get('start'),
            end_date=options.get('end'),
            **options
        )

    def handle_clear(self, segments, usernames, start_date, end_date,
                     **options):
        """Clear segments for usernames."""
        with lockfile(LOCKFILE, LOCK_EX, wait=True):
            user_segments = [get_user_segments(s, usernames,
                                               start_date=start_date,
                                               end_date=end_date)
                             for s in segments]
            # Print all the segments that will be cleared.
            for user_segment in chain(*user_segments):
                self.info(repr(user_segment), **options)
            total = sum(len(l) for l in user_segments)
            self.info('Total: %d' % total, **options)
            if not total:
                return
            # Confirm this action.
            if options.get('interactive'):
                confirm = raw_input('Clear these segments? [yN] ')
            else:
                confirm = 'y'
            # Clear segments.
            if confirm and confirm in 'yY':
                for p in chain(*user_segments):
                    p.delete()
                self.info('Cleared: %d' % total, **options)
            else:
                self.info('Aborted.', **options)

    def handle_update(self, segments, usernames, start_date, end_date,
                      **options):
        """Update segments for usernames, but only if they are missing."""
        with lockfile(LOCKFILE, LOCK_EX, wait=options['wait']):
            total = 0
            users = get_users(usernames=usernames)
            for user in users:
                for segment in segments:
                    assigned = segment.objects.assign(user=user,
                                                      start_date=start_date,
                                                      end_date=end_date)
                    if assigned:
                        self.info('Updated %r: %d' % (user, len(assigned)),
                                  **options)
                        total += len(assigned)
            self.info('Updated: %d' % total, **options)


def get_user_segments(segment, usernames=None, start_date=None, end_date=None):
    """
    Returns a QuerySet of segment objects for usernames.

    `usernames` is a list of usernames to match.
    """
    result = segment.objects.filter(site=get_current_site())
    if start_date:
        pass
    if end_date:
        pass
    if usernames:
        result = result.filter(user__in=get_users(usernames=usernames))
    return result

def get_users(usernames=None):
    result = User.objects.all()
    if usernames:
        result = result.filter(username__in=usernames)
    return result
