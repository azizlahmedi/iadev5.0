# -*- coding: utf-8 -*-
from django.urls import re_path

from neoxam.commons import views

urlpatterns = [
    re_path(r'^$', views.handle_home, name='commons-home'),
]
