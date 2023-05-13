# -*- coding: utf-8 -*-
from django.urls import re_path

from neoxam.versioning import views

urlpatterns = [
    re_path(r'^api/v1/compilation-head/(?P<schema_version>[0-9]+)/$', views.handle_compilation_head),
]
