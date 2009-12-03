# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('experiments.tests.views',
    url(r'^test-experiment/(?P<experiment_name>.*)$', 'experiment_test'),
    url(r'^test-clientsideexperiment/(?P<experiment_name>.*)$', 'clientsideexperiment_test')
)

urlpatterns += patterns('',
    url(r'^admin/', include('experiments.admin_urls')),
    url(r'^main-app/', include('experiments.urls')),
)

handler404 = 'experiments.tests.views.dummy404'
