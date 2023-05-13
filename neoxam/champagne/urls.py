# -*- coding: utf-8 -*-
from django.conf.urls import url

from neoxam.champagne import views

urlpatterns = [
    url(r'^$', views.handle_home, name='champagne-home'),
    url(r'^new/$', views.handle_new, name='champagne-new'),
    url(r'^compilations/$', views.handle_compilations, name='champagne-compilations'),
    url(r'^compilation/(?P<pk>[0-9]+)/$', views.handle_compilation, name='champagne-compilation'),
]
