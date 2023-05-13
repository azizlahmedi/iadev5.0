# -*- coding: utf-8 -*-
import datetime


class Champagne(object):
    @property
    def INSTALLED_APPS(self):
        return super(Champagne, self).INSTALLED_APPS + ['neoxam.champagne', ]

    @property
    def CELERYBEAT_SCHEDULE(self):
        super(Champagne, self).CELERYBEAT_SCHEDULE.update({
            'champagne-compilations': {
                'task': 'neoxam.champagne.tasks.beat',
                'schedule': datetime.timedelta(seconds=60),
                'options': {
                    'expires': 60,
                },
            },
        })
        return super(Champagne, self).CELERYBEAT_SCHEDULE
