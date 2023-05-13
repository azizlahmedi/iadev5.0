# -*- coding: utf-8 -*-
from django.conf import settings

VERSIONING_ALIAS = 'versioning'
VERSIONING_LABEL = 'versioning'


class VersioningRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == VERSIONING_LABEL:
            return VERSIONING_ALIAS
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == VERSIONING_LABEL:
            if not self.is_versioning_sqlite():
                raise NotImplementedError()
            return VERSIONING_ALIAS
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        if app_label == VERSIONING_LABEL:
            if not self.is_versioning_sqlite():
                return False
        return None

    def is_versioning_sqlite(self):
        return 'sqlite3' in settings.DATABASES[VERSIONING_ALIAS]['ENGINE']
