# -*- coding: utf-8 -*-
import datetime


class Versioning(object):
    @property
    def INSTALLED_APPS(self):
        return super(Versioning, self).INSTALLED_APPS + ['neoxam.versioning', ]

    @property
    def CELERYBEAT_SCHEDULE(self):
        super(Versioning, self).CELERYBEAT_SCHEDULE.update({
            'adltrack-etl-elasticsearch': {
                'task': 'neoxam.versioning.tasks.etl_elasticsearch',
                'schedule': datetime.timedelta(seconds=5 * 60),
                'options': {
                    'expires': 5 * 60,
                },
            },
        })
        return super(Versioning, self).CELERYBEAT_SCHEDULE
