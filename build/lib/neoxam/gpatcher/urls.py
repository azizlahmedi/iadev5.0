# -*- coding: utf-8 -*-
from django.urls import re_path

from neoxam.gpatcher import views

urlpatterns = [
    re_path(r'^$', views.handle_home, name='gpatcher-home'),
    re_path(r'^patch/$', views.patch_source, name='gpatcher-patch'),
    re_path(r'^result/$', views.result, name='gpatcher-result'),
]
