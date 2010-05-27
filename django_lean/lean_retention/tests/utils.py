from django.conf import settings
from django.test import TestCase as DjangoTestCase


class TestCase(DjangoTestCase):
    middleware = settings.MIDDLEWARE_CLASSES

    def _pre_setup(self):
        self.original_MIDDLEWARE_CLASSES = settings.MIDDLEWARE_CLASSES
        settings.MIDDLEWARE_CLASSES = self.middleware
        super(TestCase, self)._pre_setup()

    def _post_teardown(self):
        super(TestCase, self)._post_teardown()
        settings.MIDDLEWARE_CLASSES = self.original_MIDDLEWARE_CLASSES
