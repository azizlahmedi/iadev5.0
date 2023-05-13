# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib.staticfiles.views import serve

from neoxam.delivery import views, settings

urlpatterns = [
    url(r'^$', views.handle_home, name='delivery-home'),
    url(r'^new-delivery/$', views.handle_new_delivery, name='delivery-new-delivery'),
]
