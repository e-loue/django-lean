import logging
l = logging.getLogger(__name__)

from datetime import timedelta

from django.core.management.base import CommandError
from django.test import TestCase

from experiments.models import (Experiment, DailyEngagementReport,
                                DailyConversionReport)
from experiments.management.commands import update_experiment_reports


class TestManagement(TestCase):

    def setUp(self):
        self.experiment = Experiment(name="test_experiment")
        self.experiment.save()
        self.experiment.state = Experiment.ENABLED_STATE
        self.experiment.save()
        self.experiment.start_date = (self.experiment.start_date -
                                      timedelta(days=5))
        self.experiment.save()

    def testManageCommand(self):
        #make sure the manage.py command that generates daily stats work

        #Running with arguments should raise Exception
        self.assertRaises(CommandError,
            update_experiment_reports.Command().handle,
            "some", "args")

        #This is what manage.py will call
        self.runner = update_experiment_reports.Command().run_from_argv
        #Run the reports
        self.runner(['manage.py', 'update_experiment_reports'])

        #Make sure they were generated
        self.assertEquals(5, DailyEngagementReport.objects.filter(
                experiment=self.experiment).count())
        self.assertEquals(5, DailyConversionReport.objects.filter(
                experiment=self.experiment).count())
