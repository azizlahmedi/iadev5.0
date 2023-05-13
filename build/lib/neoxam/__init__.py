# -*- coding: utf-8 -*-
import logging
import os
from neoxam.celery import app as celery_app

# do not setup delia loggers
logging.initialized = True
__all__ = ['celery_app']
# default configuration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neoxam.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Development')

