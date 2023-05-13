# -*- coding: utf-8 -*-
from django.http.response import JsonResponse
from neoxam.adltrack import models
from neoxam.versioning import models


def handle_compilation_head(request, schema_version):
    data = []
    for procedure_name, (revision, resource_revision) in models.Compilation.objects.heads(int(schema_version)).items():
        data.append({
            'version': schema_version,
            'name': procedure_name,
            'revision': revision,
            'resource_revision': resource_revision,
        })
    return JsonResponse(data, safe=False)
