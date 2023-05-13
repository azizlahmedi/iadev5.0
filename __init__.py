# -*- coding: utf-8 -*-
import logging
import os

# do not setup delia loggers
logging.initialized = True

# default configuration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neoxam.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Development')