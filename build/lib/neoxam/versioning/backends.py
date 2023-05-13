# -*- coding: utf-8 -*-
import logging

import neoxam.elastic.backends
from neoxam.dblocks.backends import lock_backend
from neoxam.versioning import settings, models, consts

log = logging.getLogger(__name__)


class ElasticsearchBackend(neoxam.elastic.backends.ElasticBackend):
    def get_mapping(self):
        return {
            self.mapping: {
                'properties': {
                    '@timestamp': {'type': 'date'},
                    'external_id': {'type': 'integer'},
                    'procedure': {
                        'properties': {
                            'version': {'type': 'string', 'index': 'not_analyzed'},
                            'name': {'type': 'string', 'index': 'not_analyzed'},
                            'name1': {'type': 'string', 'index': 'not_analyzed'},
                            'name2': {'type': 'string', 'index': 'not_analyzed'},
                            'name3': {'type': 'string', 'index': 'not_analyzed'},
                            'name4': {'type': 'string', 'index': 'not_analyzed'},
                            'name5': {'type': 'string', 'index': 'not_analyzed'},
                            'name6': {'type': 'string', 'index': 'not_analyzed'},
                            'name7': {'type': 'string', 'index': 'not_analyzed'},
                            'name8': {'type': 'string', 'index': 'not_analyzed'},
                            'name9': {'type': 'string', 'index': 'not_analyzed'},
                        }
                    },
                    'params': {
                        'properties': {
                            'normal': {'type': 'integer'},
                            'no_save': {'type': 'integer'},
                            'list_to_file': {'type': 'integer'},
                        }
                    },
                    'success': {
                        'properties': {
                            'all': {'type': 'integer'},
                            'magnum': {'type': 'integer'},
                        }
                    },
                    'elapsed': {
                        'properties': {
                            'all': {'type': 'float'},
                            'dependencies': {'type': 'float'},
                            'magnum': {'type': 'float'},
                            'mlg': {'type': 'float'},
                            'magui': {'type': 'float'},
                            'classes': {'type': 'float'},
                            'other': {'type': 'float'},
                        }
                    }
                }
            }
        }

    def store(self, statistic):
        super().store(statistic.as_es_doc(), statistic.start)

    def batch(self, size=1000):
        """
        Return True if has more data to process.
        """
        with lock_backend.lock(consts.ELASTICSEARCH_LOCK):
            es_max_id = self.get_max_external_id()
            log.info('execute elasticsearch batch from id %d' % es_max_id)
            last_pk = es_max_id
            for statistic in models.Statistic.objects.filter(pk__gt=es_max_id).order_by('pk')[:size]:
                self.store(statistic)
                last_pk = statistic.pk
            return models.Statistic.objects.filter(pk__gt=last_pk).exists()


elasticsearch_backend = ElasticsearchBackend(
    settings.ELASTICSEARCH_URL,
    settings.ELASTICSEARCH_INDEX,
    settings.ELASTICSEARCH_MAPPING
)
