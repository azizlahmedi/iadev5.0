# -*- coding: utf-8 -*-
import multiprocessing
import os

from neoxam.settings.base import Mixin


class CrispyForms(Mixin):
    @property
    def INSTALLED_APPS(self):
        return super(CrispyForms, self).INSTALLED_APPS + ['crispy_forms', ]

    CRISPY_TEMPLATE_PACK = 'bootstrap4'

    @property
    def CRISPY_FAIL_SILENTLY(self):
        return not super(CrispyForms, self).DEBUG


class Supervisor(Mixin):
    @property
    def INSTALLED_APPS(self):
        return super(Supervisor, self).INSTALLED_APPS + ['djsupervisor', ]


class Celery(Mixin):
    # Time and date settings
    @property
    def CELERY_TIMEZONE(self):
        return self.TIME_ZONE

    # Concurrency: let 1 slots for DB and site
    CELERYD_CONCURRENCY = max(multiprocessing.cpu_count() - 1, 1)

    # Queues
    CELERY_CREATE_MISSING_QUEUES = True
    CELERY_IGNORE_RESULT = True
    CELERY_DISABLE_RATE_LIMITS = True

    # Broker
    CELERY_ACCEPT_CONTENT = ('json',)
    #CELERY_IMPORTS = ("neoxam.factory_app.tasks","neoxam.tasks")
    @property
    def BROKER_URL(self):
        return 'amqp://neoxam_user:%s@%s:5672/neoxam_vhost' % (self.RABBITMQ_PASSWORD, self.RABBITMQ_HOST)

    RABBITMQ_HOST = 'localhost'

    @property
    def RABBITMQ_PASSWORD(self):
        raise NotImplementedError('RABBITMQ_PASSWORD')

    BROKER_CONNECTION_MAX_RETRIES = 0

    # Task execution
    CELERY_TASK_SERIALIZER = 'json'

    # Beat
    CELERYBEAT_SCHEDULE = {}

    @property
    def CELERYBEAT_SCHEDULE_FILENAME(self):
        return os.path.join(self.ROOT, 'var', 'run', 'celerybeat-schedule')

    CELERYBEAT_MAX_LOOP_INTERVAL = 10

    # Logging
    CELERYD_HIJACK_ROOT_LOGGER = False
    CELERYD_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s %(name)s] %(message)s'
    CELERYD_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s %(name)s][%(task_name)s(%(task_id)s)] %(message)s'
    CELERY_REDIRECT_STDOUTS = True

    # Limits
    CELERYD_MAX_TASKS_PER_CHILD = 100
    CELERYD_TASK_SOFT_TIME_LIMIT = 25 * 60
    CELERYD_TASK_TIME_LIMIT = CELERYD_TASK_SOFT_TIME_LIMIT + 5 * 60


class RESTFramework(Mixin):
    @property
    def INSTALLED_APPS(self):
        return super(RESTFramework, self).INSTALLED_APPS + ['rest_framework', ]

    REST_FRAMEWORK = {}


class Sendfile(Mixin):
    @property
    def SENDFILE_ROOT(self):
        return os.path.join(self.ROOT, 'var', 'www', 'sendfile')

    SENDFILE_URL = "/sendfile"
