# -*- coding: utf-8 -*-
from celery import shared_task

from neoxam.versioning import backends


@shared_task(ignore_result=True)
def etl_elasticsearch():
    backends.elasticsearch_backend.batch()
