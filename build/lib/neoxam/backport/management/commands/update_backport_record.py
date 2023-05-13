import logging

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from neoxam.backport.backends import backport_backend
from neoxam.backport import consts
from neoxam.dblocks.backends import lock_backend
from neoxam.dblocks.exceptions import LockedError
from neoxam.backport import settings

log = logging.getLogger(__name__)

def notify(latest_revision):
    log.info("New commits need to be backported!")
    log.info("Sending email...")
    msg = """
    Hello,
    
    New commits need to be backported!
    
    Please go to site http://iadev-tools/backport/commits/ to check them out.
    
    Kind regards,
    
    {sender}
    """
    send_mail(
        "[{revision}] New commits need to be backported".format(revision=latest_revision),
        msg.format(sender=settings.EMAIL_SENDER),
        settings.FROM_EMAIL,
        settings.RECIPIENTS,
        fail_silently=False,
        )


class Command(BaseCommand):
    help = "Run update backport record command"

    def handle(self, *args, **options):
        try:
            with lock_backend.lock(consts.RECORD_LOCK, nowait=True):
                log.info("Updating backport record...")
                if backport_backend.get_commits_without_update(consts.FROM_VERSION, consts.TO_VERSION).exists():
                    log.debug("There is previous eligible")
                    previous_latest_eligible = backport_backend.get_commits_without_update(consts.FROM_VERSION, consts.TO_VERSION)[:1].get()
                    current_latest_eligible = backport_backend.get_commits(consts.FROM_VERSION, consts.TO_VERSION)[:1].get()
                    if current_latest_eligible.commit.revision > previous_latest_eligible.commit.revision:
                        notify(current_latest_eligible.commit.revision)
                elif backport_backend.get_commits(consts.FROM_VERSION, consts.TO_VERSION).exists():
                    log.debug("There is no previous eligible")
                    current_latest_eligible = backport_backend.get_commits(consts.FROM_VERSION, consts.TO_VERSION)[:1].get()
                    notify(current_latest_eligible.commit.revision)
                log.info("Done")
        except LockedError:
            log.info("Backport record update already running, skip...")