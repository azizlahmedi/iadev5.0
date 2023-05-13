# -*- coding: utf-8 -*-
import os

from django.conf import settings

ROOT = os.path.normpath(os.path.abspath(getattr(settings, 'HARRY_ROOT', 'harry')))

SETTINGS = getattr(settings, 'HARRY_SETTINGS', os.path.expanduser('~/.delia_mlg.cfg'))
