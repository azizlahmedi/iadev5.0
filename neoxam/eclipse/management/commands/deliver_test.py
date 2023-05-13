# -*- coding: utf-8 -*-l
import multiprocessing
import os
import tempfile
import traceback
from distutils.dir_util import copy_tree

from django.core.management.base import BaseCommand

import neoxam.champagne.backends.compiler as champagne_compiler
from factory.backends.base import untar
from neoxam.eclipse import settings, models, consts
from neoxam.factory_app import services as factory_services
from neoxam.factory_app.models import Compiler


class Command(BaseCommand):
    help = 'Deliver test'

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
        parser.add_argument(
            '-t',
            '--procedure-test-name',
            action='store',
            dest='procedure_test_name',
            help='procedure test name',
        )
        parser.add_argument(
            '-b',
            '--bundle-path',
            action='store',
            dest='bundle_path',
            help='Bundle path',
        )

    def handle(self, *args, **options):
        # Inputs
        task_id = options['task_id']
        schema_version = options['schema_version']
        procedure_name = options['procedure_name']
        procedure_test_name = options['procedure_test_name']
        bundle_path = options['bundle_path']
        # Internal use
        magnum = schema_version == 2009
        # Result
        state = consts.SUCCESS
        outputs = []
        # Global check
        try:
            # Create services
            services = factory_services.create_services(schema_version)
            # Ensure all compilers are locally installed
            compiler_homes = {}
            for compiler in Compiler.enabled_objects.all():
                with compiler.lock() as compiler_host:
                    compiler_homes[compiler.version] = compiler_host.support_home
                    services.ensure_compiler(compiler.version, compiler_host.support_home)
            # Create work folder
            with tempfile.TemporaryDirectory() as temp:
                # Paths
                app = os.path.join(temp, 'app')
                checkout = os.path.join(temp, 'checkout')
                # Extract the bundle
                untar(bundle_path, checkout)
                # Rename procedure
                services.source_backend.rename(schema_version, procedure_name, procedure_test_name, checkout)
                # Generate expanse: needs to be done before various fixes: frames & patch
                if magnum:
                    expanse_path = services.source_backend.expanse_includes(schema_version, procedure_test_name, checkout, os.path.join(temp, 'expanse.adl'))
                # Fix frame
                services.frame_area_backend.fix_local(schema_version, procedure_test_name, checkout)
                # Processes
                all_process = []
                # Compile ADL
                for compiler_version, support_home in compiler_homes.items():
                    process = multiprocessing.Process(
                        target=services.compiler_backend.compile,
                        args=(
                            support_home,
                            compiler_version,
                            checkout,
                            schema_version,
                            procedure_test_name,
                            None,
                            os.path.join(app, 'magpy', compiler_version),
                        )
                    )
                    process.start()
                    all_process.append(process)
                # I18n
                all_mo = services.i18n_backend.compile_all_po(
                    procedure_test_name,
                    os.path.join(checkout, 'gp%d' % schema_version, 'adl', 'src', 'mlg'),
                    os.path.join(app, 'mo'),
                )
                # Compile Java
                services.frame_backend.generate_and_compile_local(schema_version, procedure_test_name, all_mo, checkout, os.path.join(app, 'java'))
                # Compile expanse on MAGNUM
                if magnum:
                    with champagne_compiler.compiler_context() as magnum:
                        outputs.append(magnum.compile(procedure_test_name, expanse_path, app))
                    # No need for the schema
                    for basename in ('magnum.dbs', 'fooiu3.mq0'):
                        os.remove(os.path.join(app, 'mag', basename))
                # Join sub-processed
                for process in all_process:
                    process.join(timeout=services.compiler_backend.timeout)
                    if process.exitcode != 0:
                        raise ValueError('delia compilation failed')
                # Publish artifacts
                deliver_test_root = settings.DELIVER_TEST_ROOT.format(schema_version=schema_version)
                os.makedirs(deliver_test_root, exist_ok=True)
                copy_tree(app, deliver_test_root)
        # Something went wrong
        except:
            state = consts.FAILED
            outputs.append(traceback.format_exc())
        # Update database
        models.DeliverTestTask.objects.filter(pk=task_id).update(
            state=state,
            output='\n'.join(outputs),
        )
