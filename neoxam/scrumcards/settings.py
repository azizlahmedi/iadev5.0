# -*- coding: utf-8 -*-
from django.conf import settings

JIRA_URL = getattr(settings, 'JIRA_URL', 'https://support.neoxam.com')
JIRA_USERNAME = getattr(settings, 'JIRA_USERNAME', 'olivier.mansion')
JIRA_PASSWORD = getattr(settings, 'JIRA_PASSWORD', 'xxx')
