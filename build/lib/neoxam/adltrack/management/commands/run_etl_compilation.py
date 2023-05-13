# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from neoxam.adltrack.backends import compilation_backend


class Command(BaseCommand):
    help = 'Run compilations ETL'

    def add_arguments(self, parser):
        parser.add_argument('--initial',
                            action='store_true',
                            dest='full',
                            default=False,
                            help='Initial load')

    def handle(self, *args, **options):
        compilation_backend.collect(full=options['full'])
