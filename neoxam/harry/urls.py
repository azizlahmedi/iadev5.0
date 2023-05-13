# -*- coding: utf-8 -*-
from django.conf.urls import url

from neoxam.harry import api, views

urlpatterns = [
    url(r'^$', views.handle_home, name='harry-home'),
    url(r'^api/v1/push/$', api.PushAPIView.as_view()),
    url(r'^json/$', views.handle_json, name='harry-json'),
]
