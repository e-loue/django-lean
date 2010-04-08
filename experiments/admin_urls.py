# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib.admin.views.decorators import staff_member_required
from experiments.views import experiment_details, list_experiments

urlpatterns = patterns('experiments.views',
    url(r'^(?P<experiment_name>.+)/$', staff_member_required(experiment_details)),
    url(r'^$', staff_member_required(list_experiments))
)
