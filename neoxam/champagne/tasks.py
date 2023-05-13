# -*- coding: utf-8 -*-
import traceback

from celery import shared_task
from django.db import transaction

from neoxam.champagne import consts, models, clients
from neoxam.champagne.backends.compiler import compiler_context
from neoxam.dblocks.backends import lock_backend


@shared_task(ignore_result=True)
def compile(compilation_pk):
    with lock_backend.lock(consts.LOCK):
        # Get compilation
        compilation = models.Compilation.objects.get(pk=compilation_pk)
        # If not pending, nothing to do here
        if compilation.state != consts.PENDING:
            return
        # Only one compilation allowed
        if models.Compilation.objects.filter(state=consts.COMPILING).exists():
            return
        # Update status
        with transaction.atomic():
            compilation.state = consts.COMPILING
            compilation.save(update_fields=('state',))
    try:
        with compiler_context() as compiler:
            compilation.output = compiler.compile_and_publish(
                compilation.procedure_name,
                compilation.src.path,
                compilation.artifact_version,
                compilation.patterns.split(','),
            )
            compilation.state = consts.SUCCESS
    except Exception:
        compilation.output = traceback.format_exc()
        compilation.state = consts.FAILED
    compilation.save(update_fields=('state', 'output'))


@shared_task(ignore_result=True)
def beat():
    for compilation in models.Compilation.objects.filter(state=consts.PENDING).order_by('compiled_at'):
        clients.compile_async(compilation)
