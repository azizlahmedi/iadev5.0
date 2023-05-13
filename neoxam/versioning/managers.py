# -*- coding: utf-8 -*-
import json
import os
import collections

from django.db import models
from django.db.models import Max
from neoxam.versioning import settings


class CompilationManager(models.Manager):
    def get_queryset(self):
        return super(CompilationManager, self).get_queryset().filter(pk__gte=settings.VALID_COMPILATION_PK)

    def heads(self, schema_version):
        procedures = {}
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'gp%d_head.json' % schema_version)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as fd:
                procedures = json.load(fd)
        qs = self.filter(adlobj__version=schema_version).values_list('adlobj__name')
        qs_revision = qs.annotate(revision=Max('maxrev')).order_by('-revision')
        qs_resource_revision = qs.annotate(revision=Max('r_maxrev')).order_by('-revision')
        resource_revisions = dict(qs_resource_revision)
        for procedure_name, revision in qs_revision:
            procedures[procedure_name] = [revision, resource_revisions[procedure_name]]
        return collections.OrderedDict(sorted(procedures.items(), key=lambda e: e[1], reverse=True))
