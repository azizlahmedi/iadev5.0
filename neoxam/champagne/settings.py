# -*- coding: utf-8 -*-
import os

from django.conf import settings

ROOT_SRC = os.path.normpath(os.path.abspath(getattr(settings, 'CHAMPAGNE_ROOT_SRC', 'champagne')))

SCHEMA_NAME = getattr(settings, 'CHAMPAGNE_SCHEMA_NAME', 'portefeuille')

WSDL = getattr(settings, 'CHAMPAGNE_WSDL', 'http://neptune:44070/delia/services/Adlc?wsdl')

VMS_HOST = getattr(settings, 'CHAMPAGNE_VMS_HOST', 'venus')
VMS_USER = getattr(settings, 'CHAMPAGNE_VMS_USER', 'omansion_v')
VMS_PASSWD = getattr(settings, 'CHAMPAGNE_VMS_PASSWD', 'adlc2006')
VMS_WORK = getattr(settings, 'CHAMPAGNE_VMS_WORK', 'gpcompil/gp2009/bin')

ARTIFACTORY_USER = getattr(settings, 'CHAMPAGNE_ARTIFACTORY_USER', 'cis')
ARTIFACTORY_PASSWD = getattr(settings, 'CHAMPAGNE_ARTIFACTORY_PASSWD', 'zE0mk2A4crGS9MrTIR00')
ARTIFACTORY_URL = getattr(settings, 'CHAMPAGNE_ARTIFACTORY_URL', 'http://nx-artifacts:8085/artifactory/gp3-builds')

SUPPORT_HOME = getattr(settings, 'CHAMPAGNE_SUPPORT_HOME', '/workspace/bin/support/support-2.4.16')

LOG_HOST = getattr(settings, 'CHAMPAGNE_LOG_HOST', 'neptune')
LOG_USER = getattr(settings, 'CHAMPAGNE_LOG_USER', 'gp2006pi')
LOG_PASSWD = getattr(settings, 'CHAMPAGNE_LOG_PASSWD', 'ntic2004')
LOG_DIR = getattr(settings, 'CHAMPAGNE_LOG_DIR', '/home/gp2006pi/delia/delia/tmp')

TELNET_TIMEOUT = getattr(settings, 'CHAMPAGNE_TELNET_TIMEOUT', 60)  # in seconds
COMPILATION_TIMEOUT = getattr(settings, 'CHAMPAGNE_COMPILATION_TIMEOUT', 15 * 60)  # in seconds
