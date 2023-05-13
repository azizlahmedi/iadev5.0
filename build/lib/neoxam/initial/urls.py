# -*- coding: utf-8 -*-
from django.urls import re_path

from neoxam.initial import views

urlpatterns = [
    re_path(r'^$', views.handle_home, name='initial-home'),
]
