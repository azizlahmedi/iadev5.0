from django.core.management.base import BaseCommand
from neoxam.dblocks.backends import lock_backend
from neoxam.dblocks.exceptions import LockedError
from neoxam.initial.backends import initialcommitbackend
from neoxam.initial import consts
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Command(BaseCommand):
    help = "Synchronize the initial commit record with the adlobj"

    def handle(self, *args, **options):
        try:
            with lock_backend.lock(consts.RECORD_LOCK, nowait=True):
                log.info("Synchronizing initial commit record against adlobj...")
                initialcommitbackend.sync()
                log.info("Done")
        except LockedError:
            log.info("Initial commit record synchronization already running, skip...")
