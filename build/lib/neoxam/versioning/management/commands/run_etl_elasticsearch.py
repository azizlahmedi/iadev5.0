# -*- coding: utf-8 -*-l
from django.core.management.base import BaseCommand

from neoxam.versioning import backends


class Command(BaseCommand):
    help = 'Run Elasticsearch ETL'

    def handle(self, *args, **options):
        while backends.elasticsearch_backend.batch():
            pass
