# Django 1.6 fix
try:
    from django.conf.urls import *
except ImportError:
    from django.conf.urls.defaults import *
from django.http import HttpResponse


def home(request):
    return HttpResponse('Home')


urlpatterns = patterns('',
    url(r'^home', home, name='home'),
)
