# -*- coding: utf-8 -*-

def etl_elasticsearch_async():
    import neoxam.celery
    neoxam.celery  # load celery configuration
    from neoxam.versioning import tasks

    return tasks.etl_elasticsearch.apply_async()
