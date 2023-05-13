# -*- coding: utf-8 -*-
import logging

from neoxam.factory_app import models

log = logging.getLogger(__name__)


def compile(schema_version, procedure_name, revision, resource_revision, **kwargs):
    # Format
    procedure_name = procedure_name.lower().replace('_', '.')
    # Create the procedure objects
    procedure, _ = models.Procedure.objects.get_or_create(
        schema_version=schema_version,
        name=procedure_name,
    )
    procedure_revision, _ = models.ProcedureRevision.objects.get_or_create(
        procedure=procedure,
        revision=revision,
        resource_revision=resource_revision,
    )
    # Compile
    compile_procedure_revision(procedure_revision, **kwargs)
    # Return the procedure
    return procedure_revision


def compile_procedure_revision(procedure_revision, **kwargs):
    # Log
    log.info('ask compilation of %s', procedure_revision)
    # Create the tasks
    models.Task.objects.create_export_sources(procedure_revision, **kwargs)
    models.Task.objects.create_compile_resources(procedure_revision, **kwargs)
