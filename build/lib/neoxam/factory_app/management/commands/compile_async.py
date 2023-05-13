# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError

from neoxam.factory_app import consts, clients
from neoxam.versioning import models as versioning_models

DEFAULT_VERSION = 2009


class Command(BaseCommand):
    help = 'Asynchronous compile'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--schema',
            action='store',
            dest='schema_version',
            default=DEFAULT_VERSION,
            type=int,
            help='Schema version (default: %d)' % DEFAULT_VERSION,
        )
        parser.add_argument(
            '-n',
            '--name',
            action='store',
            dest='procedure_name',
            default=None,
            help='Procedure name',
        )
        parser.add_argument(
            '-r',
            '--revision',
            action='store',
            default=None,
            dest='revision',
            type=int,
            help='ADL revision.',
        )
        parser.add_argument(
            '-f',
            '--resource-revision',
            action='store',
            default=None,
            dest='resource_revision',
            type=int,
            help='Resources revision.',
        )

    def handle(self, *args, **options):
        # Get inputs
        schema_version = options['schema_version']
        procedure_name = options['procedure_name']
        revision = options['revision']
        resource_revision = options['resource_revision']
        # Check schema version
        if schema_version not in consts.SCHEMA_VERSIONS:
            raise CommandError('invalid schema version: %s' % schema_version)
        # Check procedure name
        if not procedure_name:
            raise CommandError('procedure name required')
        if schema_version < 2016 and not versioning_models.AdlObj.objects.filter(version=schema_version, local='mag', name=procedure_name).exists():
            raise CommandError('procedure does not exist')
        # Check revision
        if revision is None:
            raise CommandError('revision required')
        elif revision <= 0:
            raise CommandError('invalid revision: %s' % revision)
        # Check resource revision
        if resource_revision is None:
            raise CommandError('resource revision required')
        elif resource_revision <= 0:
            raise CommandError('invalid resource revision: %s' % revision)
        # Call
        clients.compile(schema_version, procedure_name, revision, resource_revision, priority=consts.HIGH, force=True)
