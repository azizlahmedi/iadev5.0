# -*- coding: utf-8 -*-

def etl_compilation_async():
    import neoxam.celery
    neoxam.celery  # load celery configuration
    from neoxam.adltrack import tasks

    return tasks.etl_compilation.apply_async()
