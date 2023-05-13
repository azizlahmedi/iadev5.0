# -*- coding: utf-8 -*-
import os

from django.conf import settings

DELIVERY_ROOT = os.path.normpath(os.path.abspath(getattr(settings, 'DELIVERY_ROOT', 'delivery_root')))