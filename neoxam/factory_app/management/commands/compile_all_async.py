# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from neoxam.factory_app import clients

from neoxam.versioning import models as versioning_models

DEFAULT_VERSION = 2009


class Command(BaseCommand):
    help = 'Asynchronous compile all from Versioning'

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

    def handle(self, *args, **options):
        # Get inputs
        schema_version = options['schema_version']
        # Iterate threw head
        for procedure_name, (revision, resource_revision) in versioning_models.Compilation.objects.heads(
                schema_version).items():
            # Send compilation
            clients.compile(schema_version, procedure_name, revision, resource_revision)
