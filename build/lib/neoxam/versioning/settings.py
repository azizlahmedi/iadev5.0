# -*- coding: utf-8 -*-
from django.conf import settings

ELASTICSEARCH_URL = getattr(settings, 'VERSIONING_ELASTICSEARCH_URL', 'http://127.0.0.1:9200')
ELASTICSEARCH_INDEX = getattr(settings, 'VERSIONING_ELASTICSEARCH_INDEX', 'versioning')
ELASTICSEARCH_MAPPING = getattr(settings, 'VERSIONING_ELASTICSEARCH_MAPPING', 'compilation')

# Before this ID the .gp3 re-generation switched binary and resource revision
VALID_COMPILATION_PK = getattr(settings, 'VERSIONING_VALID_COMPILATION_PK', 233718)
