# -*- coding: utf-8 -*-

def compile_async(compilation):
    import neoxam.celery
    neoxam.celery  # load celery configuration
    from neoxam.champagne import tasks

    return tasks.compile.apply_async(args=(compilation.pk,))
