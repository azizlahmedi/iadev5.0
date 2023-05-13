# -*- coding: utf-8 -*-
from django.conf import settings

CACHE_DIR = getattr(settings, 'BACKPORT_CACHE_DIR', '/tmp/neoxam_cache')

SVN_USERNAME = getattr(settings, 'SVN_USERNAME', 'cis')
SVN_PASSWORD = getattr(settings, 'SVN_PASSWORD', 'xxx')


FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
RECIPIENTS = [
    "olivier.mansion@neoxam.com",
    "abdellatif.ettaleb@neoxam.com",
]
