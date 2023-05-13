# -*- coding: utf-8 -*-
import logging

from celery import shared_task
from neoxam.adltrack.backends import compilation_backend

log = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def etl_compilation():
    compilation_backend.collect()


@shared_task(ignore_result=True)
def etl_commit():
    log.info('TODO: etl_commit')
