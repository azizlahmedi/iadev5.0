# -*- coding: utf-8 -*-
from celery import Celery
from configurations import importer

importer.install()

from django.conf import settings

app = Celery('neoxam')                                                    

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
