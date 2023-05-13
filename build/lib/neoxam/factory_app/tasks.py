# -*- coding: utf-8 -*-
import logging

from celery import shared_task
from django.db.models.aggregates import Max

from neoxam.dblocks.backends import lock_backend
from neoxam.factory_app import consts, models, clients, services, exceptions
from neoxam.versioning import models as versioning_models

log = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def synchronize_legacy():
    """
    Look for MAGNUM compilations and trigger Delia ones.
    """
    # Lock to do not send the order twice
    with lock_backend.lock(consts.COMPILATION_LOCK) as data:
        # Get the last processed compilation ID
        foreign_id = data.get(consts.COMPILATION_LOCK_FOREIGN_ID)
        # If not set yet, get the last 10 compilations
        if foreign_id is None:
            foreign_id_max = versioning_models.Compilation.objects.aggregate(Max('pk')).get('pk__max')
            if foreign_id_max is None:
                foreign_id_max = 0
            foreign_id = max(0, foreign_id_max - 10)  # get the last 10 compilations
        # Log
        log.info('look for compilations > %d', foreign_id)
        # Look for new ones
        qs = versioning_models.Compilation.objects.filter(
            pk__gt=foreign_id,
            adlobj__version__in=consts.SCHEMA_VERSIONS,
        ).select_related('adlobj').order_by('pk')
        # Store last compilation
        compilation = None
        # Iterate and send tasks
        for compilation in qs:
            # Send task
            clients.compile(
                compilation.adlobj.version,
                compilation.adlobj.name,
                compilation.maxrev,
                compilation.r_maxrev,
                priority=consts.HIGH,
                force=True,
            )
        # Store last processed ID
        if compilation:
            data.set(consts.COMPILATION_LOCK_FOREIGN_ID, compilation.pk)


@shared_task(ignore_result=True, expires=consts.TASK_EXPIRES)
def execute_tasks():
    for task in models.Task.objects.filter(state=consts.PENDING).order_by('priority', 'created_at'):
        task.apply_async()


@shared_task(ignore_result=True, expires=consts.TASK_EXPIRES)
def execute_task(task_pk):
    try:
        with models.Task.objects.execute(task_pk) as task:
            if task.key == consts.EXPORT_SOURCES:
                services.export_sources(task)
                for compiler in models.Compiler.enabled_objects.all():
                    models.Task.objects.create_compile(task.procedure_revision, compiler, priority=task.priority, force=True)
            elif task.key == consts.COMPILE:
                task.output = services.compile(task)
            elif task.key == consts.COMPILE_RESOURCES:
                services.compile_resources(task)
            elif task.key == consts.SYNCHRONIZE_LEGACY:
                if services.synchronize_legacy(task) and task.procedure_revision.procedure.schema_version >= 2016:
                    models.Task.objects.create_technical_tests(task.procedure_revision, priority=task.priority, force=True)
            elif task.key == consts.TECHNICAL_TESTS:
                services.technical_tests(task)
        if task.key not in (consts.SYNCHRONIZE_LEGACY, consts.TECHNICAL_TESTS) and task.procedure_revision.can_synchronize_legacy():
            models.Task.objects.create_synchronize_legacy(task.procedure_revision, priority=task.priority, force=True)
    except exceptions.TaskNotRunnable as e:
        log.info('task %s in not runnable', e.task)
    except models.Task.DoesNotExist:
        log.error('task %d does not exist', task_pk)
    except:
        log.exception('framework error on task %d', task_pk)
