# -*- coding: utf-8 -*-
from django.urls import re_path

from neoxam.backport import views

urlpatterns = [
    re_path(r'^$', views.handle_home, name='backport-home'),
    re_path(r'^commits/$', views.handle_commits, name='backport-commits'),
    re_path(r'^commits/(?P<revision>[0-9]+)/$', views.download_patch, name='backport-commit'),
    re_path(r'^commits/download/(?P<revision>[0-9]+)/$', views.download_patched_file, name='backport-commit-download'),
    re_path(r'^commits/hide/(?P<revision>[0-9]+)/$', views.hide_commit, name='backport-commit-hide')
]
