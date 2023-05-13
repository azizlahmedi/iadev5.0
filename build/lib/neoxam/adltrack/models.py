# -*- coding: utf-8 -*-
import jsonfield
from django.db import models

from neoxam.adltrack import consts


class Procedure(models.Model):
    class Meta:
        unique_together = (
            ('version', 'name'),
        )

    version = models.PositiveIntegerField(choices=consts.VERSION_CHOICES)
    name = models.CharField(max_length=255)

    def latest_version(self, **kwargs):
        qs = self.procedure_versions.all()
        if kwargs:
            qs = qs.filter(**kwargs)
        try:
            return qs.order_by('-commit__revision')[:1].get()
        except ProcedureVersion.DoesNotExist:
            pass

    def __str__(self):
        return '{}/{}'.format(self.version, self.name)

    @property
    def basename(self):
        return self.name.replace('.', '_')


class Commit(models.Model):
    class Meta:
        get_latest_by = 'revision'

    revision = models.PositiveIntegerField(unique=True)
    path = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    commit_date = models.DateTimeField()
    data = jsonfield.JSONField()

    def __str__(self):
        return '{}'.format(self.revision)


class ProcedureVersion(models.Model):
    class Meta:
        unique_together = (
            ('procedure', 'commit'),
        )

    procedure = models.ForeignKey(Procedure,on_delete=models.CASCADE, related_name='procedure_versions')
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='procedure_versions')
    data = jsonfield.JSONField()
    head = models.BooleanField(default=True)
    analyzed = models.BooleanField(default=True)
    magnum_compiled = models.BooleanField(default=False)

    def __str__(self):
        return '{}/{}@{}'.format(self.procedure.version, self.procedure.name, self.commit.revision)
