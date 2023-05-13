# -*- coding: utf-8 -*-
import os

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from neoxam.champagne import clients, models, forms, consts


class Command(BaseCommand):
    help = 'Asynchronous MAGNUM compile'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--source',
            action='store',
            dest='source_path',
            default=None,
            help='Source file.',
        )
        parser.add_argument(
            '-p',
            '--pattern',
            action='append',
            dest='patterns',
            default=[],
            help='Pattern [%s] (can be specified multiple times).' % ('|'.join(dict(consts.PATTERN_CHOICES).keys()),),
            metavar='PATTERN',
        )

    def handle(self, *args, **options):
        # self.test()
        # return
        source_path = options['source_path']
        if not source_path or not os.path.isfile(source_path):
            raise CommandError('invalid source')
        for pattern in options['patterns']:
            if pattern not in dict(consts.PATTERN_CHOICES):
                raise CommandError('invalid pattern: %s' % pattern)
        with transaction.atomic():
            with open(source_path, 'r', encoding='latin1') as fd:
                content = fd.read()
                m = forms.procedure_name_re.search(content)
                if not m:
                    raise CommandError('failed to extract procedure name')
                procedure_name = m.group(1).lower()
                fd.seek(0)
                compilation = models.Compilation.objects.create(
                    procedure_name=procedure_name,
                    src=File(fd),
                    patterns=','.join(options['patterns']),
                )
        clients.compile_async(compilation)

    def test(self):
        import tempfile
        import datetime
        from neoxam.champagne.backends.compiler import compiler_context

        with tempfile.TemporaryDirectory() as temp:
            procedure_path = os.path.join(temp, 'test.adl')
            with open(procedure_path, 'w', encoding='latin1') as fd:
                fd.write('procedure test begin type "hello world!", @cr end\n')
            with compiler_context() as compiler:
                majvac = '/workspace/src/gp/majvac.adl'
                # print(compiler.compile('test', procedure_path, datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')))
                compiler.compile('newport.gestab.lisanx', '/workspace/src/gp/lisanx.adl',
                                 datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'),
                                 [consts.FUNCTION, ])
                # compiler.compile('ach.majvac', '/home/olivier/workspace/src/newport_gesval_majvac_all.adl', datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
