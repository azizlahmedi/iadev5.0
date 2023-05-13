# -*- coding: utf-8 -*-
import datetime
import json
import logging

import requests
from requests.exceptions import HTTPError

log = logging.getLogger(__name__)


class ElasticBackend(object):
    def __init__(self, url, index, mapping, external_id_name='external_id'):
        self.url = url
        self.index = index
        self.mapping = mapping
        self.external_id_name = external_id_name
        self.session = requests.session()

    def get_index_url(self, dt=None):
        return self.url + '/' + (dt or datetime.datetime.utcnow()).strftime(self.index)

    def get_wildcard_index_url(self):
        return '%s/%s*' % (self.url, self.index_wildcard)

    def get_mapping_url(self, dt=None):
        return self.get_index_url(dt) + '/' + self.mapping

    def get_wildcard_mapping_url(self):
        return self.get_wildcard_index_url() + '/' + self.mapping

    def delete_index(self, dt=None):
        try:
            self.session.delete(self.get_index_url(dt)).raise_for_status()
        except HTTPError as e:
            if e.response.status_code != 404:
                raise

    @property
    def index_wildcard(self):
        return self.index.split('%')[0]

    def delete_all_index(self):
        # TODO: find a better implementation
        try:
            self.session.delete(self.get_wildcard_index_url()).raise_for_status()
        except HTTPError as e:
            if e.response.status_code != 404:
                raise

    def get_mapping(self):
        raise NotImplementedError('get_mapping')

    def create_index(self, dt=None):
        url = self.get_index_url(dt)
        if not self.session.head(url).ok:
            data = {'mappings': self.get_mapping(), }
            try:
                self.session.post(url, data=json.dumps(data)).raise_for_status()
            except HTTPError as e:
                if e.response.status_code != 400:  # created simultaneously
                    raise

    def store(self, data, dt=None):
        self.create_index(dt)
        response = self.session.post(self.get_mapping_url(dt), data=json.dumps(data))
        response.raise_for_status()

    def get_max_external_id(self):
        query = {'sort': [{self.external_id_name: {'order': 'desc'}}], 'size': 1}
        response = self.session.get(self.get_wildcard_mapping_url() + '/_search', data=json.dumps(query))
        if response.status_code in (400,):  # index not created
            return -1
        response.raise_for_status()
        hits = response.json()['hits']['hits']
        if not hits:
            return -1
        return hits[0]['_source'][self.external_id_name]
