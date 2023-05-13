# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone
from neoxam.harry import settings

fs = FileSystemStorage(location=settings.ROOT)


def untranslated_upload_to(instance, filename):
    return 'untranslated/{0}/{1}/{2}'.format(instance.hostname, instance.procedure_name.replace('.', '_'), filename)


def json_upload_to(_instance, filename):
    return 'json/{0}/{1}'.format(timezone.now().strftime('%Y/%m'), filename)


class Push(models.Model):
    procedure_name = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255)
    session_id = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    file = models.FileField(upload_to=untranslated_upload_to, storage=fs)
    creation_date = models.DateTimeField(default=timezone.now)


class JsonUntranslated(models.Model):
    username = models.CharField(max_length=32)
    comment = models.TextField()
    file = models.FileField(upload_to=json_upload_to, storage=fs)
    creation_date = models.DateTimeField(default=timezone.now)
