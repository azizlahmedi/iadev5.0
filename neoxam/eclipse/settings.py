# -*- coding: utf-8 -*-
import os

from django.conf import settings

TMP = os.path.normpath(os.path.abspath(getattr(settings, 'ECLIPSE_TMP', 'eclipse_tmp')))

PUBLISH_ROOT = os.path.normpath(os.path.abspath(getattr(settings, 'ECLIPSE_PUBLISH_ROOT', 'eclipse_publish_root')))
PUBLISH_URL = getattr(settings, 'ECLIPSE_PUBLISH_URL', 'file://' + PUBLISH_ROOT)
if not PUBLISH_URL.endswith('/'):
    PUBLISH_URL += '/'

DELIVER_TEST_ROOT = os.path.normpath(os.path.abspath(getattr(settings, 'ECLIPSE_DELIVER_TEST_ROOT', 'eclipse_deliver_test_root/{schema_version}')))

SVN_URL = getattr(settings, 'ECLIPSE_SVN_URL', 'http://avalon.bams.corp:3180/svn/repos/gp/trunk/')
if not SVN_URL.endswith('/'):
    SVN_URL += '/'
SVN_USERNAME = getattr(settings, 'SVN_USERNAME', 'cis')
SVN_PASSWORD = getattr(settings, 'SVN_PASSWORD', 'Ntic2007')

ELASTICSEARCH_URL = getattr(settings, 'ECLIPSE_ELASTICSEARCH_URL', 'http://127.0.0.1:9200')
ELASTICSEARCH_INDEX = getattr(settings, 'ECLIPSE_ELASTICSEARCH_INDEX', 'eclipse')
ELASTICSEARCH_MAPPING = getattr(settings, 'ECLIPSE_ELASTICSEARCH_MAPPING', 'eclipse')

RUNTIME_URL = getattr(settings, 'ECLIPSE_RUNTIME_URL', 'http://nx-artifacts:8085/artifactory/gp3-binaries/runtime/')
if not RUNTIME_URL.endswith('/'):
    RUNTIME_URL += '/'
