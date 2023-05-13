# -*- coding: utf-8 -*-
import contextlib
import logging
import traceback

from django.db import models, transaction
from django.utils import timezone

from neoxam.factory_app import consts, exceptions

log = logging.getLogger(__name__)


class EnabledCompilerManager(models.Manager):
    def get_queryset(self):
        return super(EnabledCompilerManager, self).get_queryset().filter(enabled=True)

    def get_compatibility_versions(self, services):
        for compiler in self.filter(compatibility_version=''):
            with compiler.lock() as compiler_host:
                compiler.compatibility_version = services.ensure_compiler(compiler.version, compiler_host.support_home)
            compiler.save(update_fields=('compatibility_version',))
        return self.values_list('compatibility_version', flat=True)


class TaskManager(models.Manager):
    @contextlib.contextmanager
    def execute(self, task_pk):
        with transaction.atomic():
            log.info('lock task %s', task_pk)
            task = self.select_for_update(nowait=False).get(pk=task_pk)
            log.info('task %s locked', task)
            if task.state != consts.PENDING:
                log.info('task %s is not runnable as its state is %s', task_pk, task.state)
                raise exceptions.TaskNotRunnable(task)
            task.state = consts.RUNNING
            task.started_at = timezone.now()
            task.save(update_fields=('state', 'started_at'))
        log.info('start task %s', task_pk)
        try:
            yield task
        except Exception as e:
            output = ''
            if hasattr(e, 'output'):
                exc_output = None
                if isinstance(e.output, bytes):
                    exc_output = e.output.decode('utf-8', 'replace')
                elif isinstance(e.output, str):
                    exc_output = e.output
                if exc_output is not None:
                    output += exc_output.replace('\r', '').rstrip('\n') + '\n' + 80 * '-' + '\n'
            output += traceback.format_exc()
            state = consts.FAILED
            log.error('task %s failed:\n%s', task_pk, output)
        else:
            output = task.output
            state = consts.SUCCESS
            log.info('task %s successful', task_pk)
        with transaction.atomic():
            self.filter(pk=task_pk).update(
                state=state,
                output=output,
                completed_at=timezone.now()
            )

    def _create(self, key, procedure_revision, compiler=None, **kwargs):
        force = kwargs.pop('force', False)
        with transaction.atomic():
            task, created = self.get_or_create(
                key=key,
                procedure_revision=procedure_revision,
                compiler=compiler,
                defaults=kwargs,
            )
            if force:
                log.info('lock task %s', task)
                task = self.select_for_update(nowait=False).get(pk=task.pk)
                log.info('task %s locked', task)
                if task.state in consts.FINAL_STATES:
                    task.priority = kwargs.get('priority', consts.NORMAL)
                    task.reset(save=True)
                log.info('unlock task %s', task)
        if task.state == consts.PENDING:
            task.apply_async()
        return task, created

    def create_export_sources(self, procedure_revision, **kwargs):
        return self._create(consts.EXPORT_SOURCES, procedure_revision=procedure_revision, **kwargs)

    def create_compile(self, procedure_revision, compiler, **kwargs):
        return self._create(consts.COMPILE, procedure_revision=procedure_revision, compiler=compiler, **kwargs)

    def create_compile_resources(self, procedure_revision, **kwargs):
        return self._create(consts.COMPILE_RESOURCES, procedure_revision=procedure_revision, **kwargs)

    def create_synchronize_legacy(self, procedure_revision, **kwargs):
        return self._create(consts.SYNCHRONIZE_LEGACY, procedure_revision=procedure_revision, **kwargs)

    def create_technical_tests(self, procedure_revision, **kwargs):
        return self._create(consts.TECHNICAL_TESTS, procedure_revision=procedure_revision, **kwargs)
