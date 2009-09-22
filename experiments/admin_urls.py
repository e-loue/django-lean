from django.conf.urls.defaults import *

urlpatterns = patterns('experiments.views',
                       url(r'^(?P<experiment_name>.+)/$',
                           'experiment_details'),
                       url(r'^$', 'list_experiments'))
