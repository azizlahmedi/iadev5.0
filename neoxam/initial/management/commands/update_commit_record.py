from django.core.management.base import BaseCommand
from neoxam.dblocks.backends import lock_backend
from neoxam.dblocks.exceptions import LockedError
from neoxam.initial import consts
from neoxam.initial.backends import initialcommitbackend
from django.core.mail import send_mail
from neoxam.initial import settings
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def notify(latest_revision):
    log.info("New initial commits!")
    log.info("Sending email...")
    msg = """Hello,

New initial commits arrived!

Please go to site http://iadev-tools/initial/ to check them out.

Kind regards,

{sender}
"""
    send_mail(
        "[{revision}] New initial commits!".format(revision=latest_revision),
        msg.format(sender=settings.EMAIL_SENDER),
        settings.FROM_EMAIL,
        settings.RECIPIENTS,
        fail_silently=False,
    )


class Command(BaseCommand):
    help = "Run update initial commit record command"

    def handle(self, *args, **options):
        try:
            with lock_backend.lock(consts.RECORD_LOCK, nowait=True):
                log.info("Updating initial commit record...")
                if len(initialcommitbackend.get_initial_commits_without_update(consts.VERSION)) != 0:
                    log.debug("There is previous eligible")
                    previous_latest_eligible = initialcommitbackend.get_initial_commits_without_update(consts.VERSION)[
                                               :1].get()
                    current_latest_eligible = initialcommitbackend.get_initial_commits(consts.VERSION)[:1].get()
                    if current_latest_eligible.revision > previous_latest_eligible.revision:
                        notify(current_latest_eligible.revision)
                elif len(initialcommitbackend.get_initial_commits(consts.VERSION)) != 0:
                    log.debug("There is no previous eligible")
                    current_latest_eligible = initialcommitbackend.get_initial_commits(consts.VERSION)[:1].get()
                    notify(current_latest_eligible.revision)
                log.info("Done")
        except LockedError:
            log.info("Initial commit record update already running, skip...")
