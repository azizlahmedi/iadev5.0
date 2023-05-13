# -*- coding: utf-8 -*-
import os
from celery import Celery

from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neoxam.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Development')

app = Celery('neoxam',
              include=['neoxam.factory_app.tasks','neoxam.tasks'])

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
