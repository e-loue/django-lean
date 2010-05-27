from django.conf.urls.defaults import *
from django.http import HttpResponse


def home(request):
    return HttpResponse('Home')


urlpatterns = patterns('',
    url(r'^home', home, name='home'),
)
