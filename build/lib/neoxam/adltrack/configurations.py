# -*- coding: utf-8 -*-
import datetime


class ADLTrack(object):
    @property
    def INSTALLED_APPS(self):
        return super(ADLTrack, self).INSTALLED_APPS + ['neoxam.adltrack', ]

    @property
    def CELERYBEAT_SCHEDULE(self):
        super(ADLTrack, self).CELERYBEAT_SCHEDULE.update({
            'adltrack-etl-compilation': {
                'task': 'neoxam.adltrack.tasks.etl_compilation',
                'schedule': datetime.timedelta(seconds=5 * 60),
                'options': {
                    'expires': 5 * 60,
                },
            },
            'adltrack-etl-commit': {
                'task': 'neoxam.adltrack.tasks.etl_commit',
                'schedule': datetime.timedelta(seconds=5 * 60),
                'options': {
                    'expires': 5 * 60,
                },
            },
        })
        return super(ADLTrack, self).CELERYBEAT_SCHEDULE
