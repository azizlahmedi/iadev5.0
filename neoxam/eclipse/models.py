# -*- coding: utf-8 -*-
import uuid

import jsonfield
from django.db import models
from django.utils import timezone

from neoxam.eclipse import managers, settings, consts


class Stats(models.Model):
    date = models.DateTimeField()
    action = models.CharField(max_length=255)
    schema_version = models.PositiveIntegerField()
    procedure_name = models.CharField(max_length=255)
    success = models.BooleanField()
    data = jsonfield.JSONField()

    objects = managers.StatsManager()

    def as_es_doc(self):
        data = {
            '@timestamp': self.data['timestamp'],
            'external_id': self.pk,
            'action': self.action,
            'elapsed': self.data['elapsed'],
            'success': int(self.success),
            'exception': self.data['exception'],
            'procedure': {
                'version': self.schema_version,
                'name': self.procedure_name,
            },
            'env': {
                'session': self.data['session'],
                'hostname': self.data['hostname'],
                'username': self.data['username'],
                'platform_system': self.data['platform_system'],
                'platform_release': self.data['platform_release'],
                'platform_version': self.data['platform_version'],
                'python_version': self.data['python_version'],
                'compiler_version': self.data['compiler_version'],
            },
        }
        for index, name in list(enumerate(self.procedure_name.split('.'), start=1))[:9]:
            data['procedure']['name%d' % index] = name
        return data


class Runtime(models.Model):
    version = models.CharField(max_length=32)
    enabled = models.BooleanField(default=False)
    release_date = models.DateTimeField()

    @property
    def url(self):
        return settings.RUNTIME_URL + '{version}/runtime-{version}-win-amd64.zip'.format(version=self.version)


class DeliverTestTask(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    schema_version = models.PositiveIntegerField()
    procedure_name = models.CharField(max_length=255)
    procedure_test_name = models.CharField(max_length=255)
    state = models.CharField(max_length=32, choices=consts.STATE_CHOICES, default=consts.COMPILING)
    output = models.TextField(blank=True)

    def as_json(self):
        return {
            'pk': self.pk,
            'state': self.state,
            'output': self.output,
        }
