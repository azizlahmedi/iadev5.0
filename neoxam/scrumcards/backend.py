# -*- coding: utf-8 -*-
import datetime

import requests

from neoxam.scrumcards import settings
from neoxam.scrumcards.exceptions import NoSuchSprint

EMPTY_KEY = 25 * ' '


class EmptyCard(object):
    key = EMPTY_KEY
    summary = ''
    issue_type = 5 * ' '
    subtasks = [EMPTY_KEY, ]
    parent = EMPTY_KEY
    estimate = 5 * ' '
    points = None


empty_card = EmptyCard()


class Card(object):
    def __init__(self, raw):
        self.raw = raw

    @property
    def key(self):
        """DELIA-999"""
        return self.raw['key']

    @property
    def summary(self):
        """Subject"""
        return self.raw['fields']['summary']

    @property
    def issue_type(self):
        return self.raw['fields']['issuetype']['name']

    @property
    def subtasks(self):
        return [raw_task['key'] for raw_task in self.raw['fields']['subtasks']]

    @property
    def parent(self):
        return self.raw['fields'].get('parent', {}).get('key')

    @property
    def estimate(self):
        return datetime.timedelta(seconds=self.raw['fields']['aggregateprogress']['total'])

    @property
    def points(self):
        """
        customfield_10241 = original story points
        customfield_10403 = story points
        """
        return self.raw['fields'].get('customfield_12462')

    def __str__(self):
        return self.key


class Backend(object):
    def __init__(self, url=settings.JIRA_URL, username=settings.JIRA_USERNAME, password=settings.JIRA_PASSWORD,
                 verify=False):
        self.url = url
        self.username = username
        self.password = password
        self.verify = verify

    def get(self, sprint_id):
        auth = (self.username, self.password)
        search_url = self.url + '/rest/api/latest/search'
        params = {'jql': 'sprint=%d' % sprint_id}
        response = requests.get(search_url, params=params, auth=auth, verify=self.verify)
        if response.status_code == requests.codes.BAD_REQUEST:
            raise NoSuchSprint(sprint_id)
        response.raise_for_status()
        payload = response.json()
        return [Card(raw) for raw in payload['issues']]


backend = Backend()
