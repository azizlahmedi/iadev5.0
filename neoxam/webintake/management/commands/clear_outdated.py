# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand

from neoxam.webintake.backends import clean_up_users

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clear outdated record."

    def handle(self, *args, **options):
        log.info("Clearing outdated user record.")
        clean_up_users()
