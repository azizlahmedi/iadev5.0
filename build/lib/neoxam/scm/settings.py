# -*- coding: utf-8 -*-
import os

from django.conf import settings

CHECKOUT_DIR = os.path.normpath(os.path.abspath(getattr(settings, 'SCM_CHECKOUT_DIR', 'scm')))
