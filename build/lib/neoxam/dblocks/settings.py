# -*- coding: utf-8 -*-
from django.conf import settings

DATABASE_ALIAS = getattr(settings, 'DBLOCKS_DATABASE_ALIAS', 'default')
