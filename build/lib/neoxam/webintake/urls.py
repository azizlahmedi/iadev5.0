# -*- coding: utf-8 -*-
from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns

from neoxam.webintake import api

urlpatterns = [
    re_path(r'^api/user/push/$', api.create_update_user),
    re_path(r'^api/user/get/(?P<user_name>[\w.]+)/$', api.retrieve_delete_user),
]

urlpatterns = format_suffix_patterns(urlpatterns)
