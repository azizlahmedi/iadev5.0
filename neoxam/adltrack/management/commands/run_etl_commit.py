# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand

from neoxam.adltrack import consts
from neoxam.adltrack.backends import analysis_backend
from neoxam.dblocks.backends import lock_backend
from neoxam.dblocks.exceptions import LockedError

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run commits ETL'

    def add_arguments(self, parser):
        parser.add_argument('--initial',
                            action='store_true',
                            dest='full',
                            default=False,
                            help='Initial load')

    def handle(self, *args, **options):
        try:
            with lock_backend.lock(consts.COMMIT_LOCK, nowait=True):
                analysis_backend.process(full=options['full'])
        except LockedError:
            log.info('ETL already running, skip...')
