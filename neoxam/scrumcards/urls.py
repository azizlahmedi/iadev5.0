# -*- coding: utf-8 -*-
from django.conf.urls import url
from neoxam.scrumcards import views

urlpatterns = [
    url(r'^$', views.handle_home, name='scrumcards-home'),
]
