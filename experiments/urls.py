# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('experiments.views',
    url(r'^goal/(?P<goal_name>.*)$', 'record_experiment_goal'),
    url(r'^confirm_human/$', 'confirm_human')
)

urlpatterns += patterns('',
    url(r'^admin/', include('experiments.admin_urls')),
)
