# -*- coding: utf-8 -*-l
import traceback

from django.core.management.base import BaseCommand
from neoxam.factory_app import models, consts
from neoxam.factory_app import services as factory_services


class Command(BaseCommand):
    help = 'Compile legacy'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--id',
            action='store',
            dest='task_id',
            help='task id',
            type=int,
        )
        parser.add_argument(
            '-s',
            '--schema-version',
            action='store',
            dest='schema_version',
            help='schema version',
            type=int,
        )
        parser.add_argument(
            '-n',
            '--procedure-name',
            action='store',
            dest='procedure_name',
            help='procedure name',
        )

    def handle(self, *args, **options):
        # Inputs
        task_id = options['task_id']
        schema_version = options['schema_version']
        procedure_name = options['procedure_name']
        # Result
        state = consts.SUCCESS
        output = ''
        # Global check
        try:
            # Create services
            services = factory_services.create_services(schema_version)
            # Ensure all compilers are locally installed
            compiler_homes = {}
            for compiler in models.Compiler.enabled_objects.all():
                with compiler.lock() as compiler_host:
                    compiler_homes[compiler.version] = compiler_host.support_home
                    services.ensure_compiler(compiler.version, compiler_host.support_home)
            # Create work folder
            services.compile_legacy(schema_version, procedure_name, compiler_homes)
        # Something went wrong
        except:
            state = consts.FAILED
            output = traceback.format_exc()
        # Update database
        models.CompileLegacyTask.objects.filter(pk=task_id).update(
            state=state,
            output=output,
        )
