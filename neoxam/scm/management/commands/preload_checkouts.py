# -*- coding: utf-8 -*-
import multiprocessing

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from neoxam.scm import models, backends


class Command(BaseCommand):
    help = 'Pre-load repository checkouts'

    def add_arguments(self, parser):
        parser.add_argument(
            '-n'
            '--number',
            action='store',
            dest='number',
            type=int,
            default=getattr(settings, 'CELERYD_CONCURRENCY', multiprocessing.cpu_count()) + 1,
            help='Number of checkouts per repository',
        )

    def handle(self, *args, **options):
        number = options['number']
        if number < 0:
            raise CommandError('positive integer expected')
        for repository in models.Repository.objects.all():
            self._preload(repository, 0, number)

    def _preload(self, repository, current_number, target_number):
        if current_number >= target_number:
            return
        with backends.repository_backend.checkout_context(repository.key) as scm_backend:
            scm_backend.checkout()
            self._preload(repository, current_number + 1, target_number)
