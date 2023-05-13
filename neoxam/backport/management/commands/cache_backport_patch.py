import logging

from django.core.management.base import BaseCommand
from neoxam.backport.backends import backport_backend
from neoxam.backport import consts

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Run cache backport patch command"

    def handle(self, *args, **options):
        for record in backport_backend.get_commits(consts.FROM_VERSION, consts.TO_VERSION):
            log.debug('Caching patch for commit: {} to version: {}'.format(record.commit, consts.TO_VERSION))
            backport_backend.get_patch(record.commit, consts.TO_VERSION)
