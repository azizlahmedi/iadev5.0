# -*- coding: utf-8 -*-
from django.urls import re_path
from neoxam.factory_app import views

urlpatterns = [
    re_path(r'^$', views.handle_home, name='factory-home'),
    re_path(r'^tasks/$', views.handle_tasks, name='factory-tasks'),
    re_path(r'^task/(?P<pk>[0-9]+)/$', views.handle_task, name='factory-task'),
    re_path(r'^batches/$', views.handle_batches, name='factory-batches'),
    re_path(r'^batch/(?P<pk>[0-9]+)/$', views.handle_batch, name='factory-batch'),
    re_path(r'^new-batch/$', views.handle_new_batch, name='factory-new-batch'),
    re_path(r'^batch/(?P<pk>[0-9]+)/retry/$', views.handle_batch_retry, name='factory-batch-retry'),
    re_path(r'^compile-legacy/$', views.handle_compile_legacy, name='factory-compile-legacy'),
    re_path(r'^compile-legacy-tasks/$', views.handle_compile_legacy_tasks, name='factory-compile-legacy-tasks'),
    re_path(r'^compile-legacy-task/(?P<pk>[0-9]+)/$', views.handle_compile_legacy_task, name='factory-compile-legacy-task'),
    re_path(r'^trads/$', views.handle_trad, name='factory-trads'),
    re_path(r'^upload-trads/$', views.handle_upload, name='factory-uplpoad-trads'),


    ]