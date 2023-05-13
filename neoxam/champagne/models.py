# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

from neoxam.champagne import settings, consts

fs_src = FileSystemStorage(location=settings.ROOT_SRC)


class Compilation(models.Model):
    procedure_name = models.CharField(max_length=255, blank=False)
    state = models.CharField(max_length=16, choices=consts.STATE_CHOICES, default=consts.PENDING)
    compiled_at = models.DateTimeField(default=timezone.now)
    output = models.TextField(blank=True)
    src = models.FileField(storage=fs_src, verbose_name='Source', upload_to='%Y/%m')
    patterns = models.CharField(max_length=255, blank=True)

    @property
    def artifact_version(self):
        return self.compiled_at.strftime('%Y%m%d%H%M%S')

    @property
    def artifact_url(self):
        if self.state != consts.SUCCESS:
            return ''
        return '{url}/{procedure_name}/{version}/{procedure_name}-{version}.tgz'.format(
            url=settings.ARTIFACTORY_URL,
            procedure_name=self.procedure_name,
            version=self.artifact_version,
        )
