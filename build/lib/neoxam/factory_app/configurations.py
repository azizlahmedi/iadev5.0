# -*- coding: utf-8 -*-
import datetime

from neoxam.factory_app import consts


class Factory(object):
    @property
    def INSTALLED_APPS(self):
        return super(Factory, self).INSTALLED_APPS + ['neoxam.factory_app', ]

    @property
    def CELERYBEAT_SCHEDULE(self):
        super(Factory, self).CELERYBEAT_SCHEDULE.update({
            'factory-synchronize-legacy': {
                'task': 'neoxam.factory_app.tasks.synchronize_legacy',
                'schedule': datetime.timedelta(seconds=30),
                'options': {
                    'expires': 30,
                },
            },
            'factory-execute-tasks': {
                'task': 'neoxam.factory_app.tasks.execute_tasks',
                'schedule': datetime.timedelta(seconds=consts.TASK_EXPIRES),
                'options': {
                    'expires': consts.TASK_EXPIRES,
                },
            },
        })
        return super(Factory, self).CELERYBEAT_SCHEDULE
