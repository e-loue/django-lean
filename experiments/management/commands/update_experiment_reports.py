import logging
l=logging.getLogger(__name__)

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from experiments.reports import (ActivityReportGenerator,
                                       ConversionReportGenerator)

class Command(BaseCommand):
    help = ('update_experiment_reports : Generate all the daily reports for'
            ' for the SplitTesting experiments')

    def __init__(self):
        super(self.__class__, self).__init__()

    def handle(self, *args, **options):
        if len(args):
            raise CommandError("This command does not take any arguments")

        engagement_calculator = _load_function(settings.LEAN_ENGAGEMENT_CALCULATOR)

        ActivityReportGenerator(activity_score_calculator=engagement_calculator).generate_all_daily_reports()
        ConversionReportGenerator().generate_all_daily_reports()

def _load_function(fully_qualified_name):
    i = fully_qualified_name.rfind('.')
    module, attr = fully_qualified_name[:i], fully_qualified_name[i+1:]
    try:
        mod = __import__(module, globals(), locals(), [attr])
    except ImportError, e:
        raise ImproperlyConfigured, 'Error importing template source loader %s: "%s"' % (module, e)
    try:
        func = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured, 'Module "%s" does not define a "%s" callable template source loader' % (module, attr)
    return func
