# -*- coding: utf-8 -*-
import os

from django.conf import settings


SETTINGS = getattr(settings, 'FACTORY_SETTINGS', os.path.expanduser('~/.factory.cfg'))

SUPPORT_HOMES = os.path.normpath(getattr(settings, 'FACTORY_SUPPORT_HOMES', 'support_homes'))

SVN_URL = getattr(settings, 'FACTORY_SVN_URL', 'http://avalon.bams.corp:3180/svn/repos/gp/trunk/')
if not SVN_URL.endswith('/'):
    SVN_URL += '/'
SVN_USERNAME = getattr(settings, 'SVN_USERNAME', 'cis')
SVN_PASSWORD = getattr(settings, 'SVN_PASSWORD', 'Ntic2007')
