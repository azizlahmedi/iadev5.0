# -*- coding: utf-8 -*-
import contextlib
import logging

from django.db import DatabaseError, transaction
from neoxam.dblocks import models, settings, exceptions

log = logging.getLogger(__name__)


class Data(object):
    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value


class LockBackend(object):
    @contextlib.contextmanager
    def lock(self, name, nowait=False):
        models.Lock.objects.using(settings.DATABASE_ALIAS).get_or_create(name=name)
        with transaction.atomic(using=settings.DATABASE_ALIAS):
            log.info('lock %s', name)
            try:
                lock = models.Lock.objects.using(settings.DATABASE_ALIAS).select_for_update(nowait=nowait).get(
                    name=name)
            except DatabaseError:
                raise exceptions.LockedError(name)
            log.info('%s locked', name)
            yield Data(lock.data)
            log.info('unlock %s', name)
            lock.save(using=settings.DATABASE_ALIAS, update_fields=('data',))


lock_backend = LockBackend()
