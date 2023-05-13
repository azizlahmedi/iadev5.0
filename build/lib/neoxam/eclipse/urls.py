# -*- coding: utf-8 -*-
from django.urls import re_path

from neoxam.eclipse import views

urlpatterns = [
    re_path(r'^$', views.handle_home, name='eclipse-home'),
    re_path(r'^compile/$', views.handle_compile, name='eclipse-compile'),
    re_path(r'^deliver/$', views.handle_deliver, name='eclipse-deliver'),
    re_path(r'^deliver-test/$', views.handle_new_deliver_test, name='eclipse-new-deliver-test'),
    re_path(r'^deliver-test/(?P<pk>[0-9]+)/$', views.handle_deliver_test, name='eclipse-deliver-test'),
    re_path(r'^stats/$', views.handle_stats, name='eclipse-stats'),
    re_path(r'^runtime/$', views.handle_runtime, name='eclipse-runtime'),
]
