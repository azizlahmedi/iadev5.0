# -*- coding: utf-8 -*-
import tempfile

import factory.services
from neoxam.factory_app import settings, models


def export_sources(task):
    procedure_revision = task.procedure_revision
    with procedure_revision.lock():
        schema_version = procedure_revision.procedure.schema_version
        services = create_services(schema_version)
        services.export_sources(
            schema_version,
            procedure_revision.procedure.name,
            procedure_revision.revision,
        )


def compile(task):
    compiler = task.compiler
    procedure_revision = task.procedure_revision
    schema_version = procedure_revision.procedure.schema_version
    services = create_services(schema_version)
    with compiler.lock() as compiler_host:
        services.ensure_compiler(compiler.version, compiler_host.support_home)
    with tempfile.TemporaryDirectory() as app:
        output = services.compile(
            schema_version,
            procedure_revision.procedure.name,
            procedure_revision.revision,
            compiler.version,
            compiler_host.support_home,
            app,
        )
        _synchronize(task, app)
        return output
    


def compile_resources(task):
    procedure_revision = task.procedure_revision
    with tempfile.TemporaryDirectory() as app:
        schema_version = procedure_revision.procedure.schema_version
        services = create_services(schema_version)
        services.compile_resources(
            schema_version,
            procedure_revision.procedure.name,
            procedure_revision.resource_revision,
            'HEAD',
            procedure_revision.resource_revision,
            procedure_revision.resource_revision,
            app,
        )
        _synchronize(task, app)


def _synchronize(task, app):
    procedure_revision = task.procedure_revision
    with procedure_revision.procedure.lock():
        schema_version = procedure_revision.procedure.schema_version
        services = create_services(schema_version)
        services.synchronize(
            schema_version,
            procedure_revision.procedure.name,
            procedure_revision.revision,
            procedure_revision.resource_revision,
            app,
            models.Compiler.enabled_objects.get_compatibility_versions(services),
        )


def synchronize_legacy(task):
    procedure_revision = task.procedure_revision
    with procedure_revision.procedure.lock():
        if procedure_revision.can_synchronize_legacy():
            schema_version = procedure_revision.procedure.schema_version
            services = create_services(schema_version)
            services.synchronize_legacy(
                schema_version,
                procedure_revision.procedure.name,
                procedure_revision.revision,
                procedure_revision.resource_revision,
            )
            return True
    return False


def technical_tests(task):
    procedure_revision = task.procedure_revision
    schema_version = procedure_revision.procedure.schema_version
    services = create_services(schema_version)
    services.technical_tests(
        schema_version,
        procedure_revision.procedure.name,
        procedure_revision.revision,
        procedure_revision.resource_revision,
        sandbox=True,
    )


def create_services(schema_version):
    return factory.services.create_services(settings.SETTINGS % {'schema_version': schema_version})
