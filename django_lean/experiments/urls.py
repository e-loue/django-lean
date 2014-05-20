# -*- coding: utf-8 -*-
# Django 1.6 fix
try:
    from django.conf.urls import *
except ImportError:
    from django.conf.urls.defaults import *


urlpatterns = patterns('django_lean.experiments.views',
    url(r'^goal/(?P<goal_name>.*)$', 'record_experiment_goal'),
    url(r'^confirm_human/$', 'confirm_human')
)
