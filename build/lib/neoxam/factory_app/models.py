# -*- coding: utf-8 -*-
import contextlib
import logging
import os
import socket

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from neoxam.factory_app import consts, managers, settings

log = logging.getLogger(__name__)


class Compiler(models.Model):
    class Meta:
        app_label = 'factory_app'
        
    version = models.CharField(max_length=32, unique=True, blank=False)
    enabled = models.BooleanField(default=False)
    compatibility_version = models.CharField(max_length=32, blank=True, editable=False)

    @contextlib.contextmanager
    def lock(self, nowait=False):
        """
        Lock the compiler on the current host.
        """
        compiler_host, _ = CompilerHost.objects.get_or_create(compiler=self, hostname=socket.gethostname())
        with transaction.atomic():
            log.info('lock compiler %s', compiler_host)
            compiler_host = CompilerHost.objects.select_for_update(nowait=nowait).get(pk=compiler_host.pk)
            log.info('compiler %s locked', compiler_host)
            yield compiler_host
            log.info('unlock compiler %s', compiler_host)

    objects = models.Manager()
    enabled_objects = managers.EnabledCompilerManager()

    def __str__(self):
        return self.version


class CompilerHost(models.Model):
    class Meta:
        app_label = 'factory_app'
        unique_together = (
            ('compiler', 'hostname'),
        )

    compiler = models.ForeignKey(Compiler ,on_delete=models.CASCADE)
    hostname = models.CharField(max_length=255, blank=False)

    @property
    def support_home(self):
        return os.path.join(settings.SUPPORT_HOMES, self.compiler.version)

    def __str__(self):
        return '%s@%s' % (self.compiler.version, self.hostname)


class Procedure(models.Model):
    class Meta:
        app_label = 'factory_app'
        unique_together = (
            ('schema_version', 'name'),
        )

    schema_version = models.PositiveIntegerField(choices=consts.SCHEMA_VERSION_CHOICES)
    name = models.CharField(max_length=255)

    @contextlib.contextmanager
    def lock(self, nowait=False):
        """
        Lock the compiler on the current host.
        """
        with transaction.atomic():
            log.info('lock procedure %s', self)
            procedure = self.__class__.objects.select_for_update(nowait=nowait).get(pk=self.pk)
            log.info('procedure %s locked', procedure)
            yield procedure
            log.info('unlock procedure %s', procedure)

    def __str__(self):
        return '%d:%s' % (self.schema_version, self.name)


class ProcedureRevision(models.Model):
    class Meta:
        app_label = 'factory_app' 
        unique_together = (
            ('procedure', 'revision', 'resource_revision'),
        )

    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    resource_revision = models.PositiveIntegerField()

    @contextlib.contextmanager
    def lock(self, nowait=False):
        """
        Lock the compiler on the current host.
        """
        with transaction.atomic():
            log.info('lock procedure revision %s', self)
            procedure_revision = self.__class__.objects.select_for_update(nowait=nowait).get(pk=self.pk)
            log.info('procedure revision %s locked', procedure_revision)
            yield procedure_revision
            log.info('unlock procedure revision %s', procedure_revision)

    def is_head(self):
        """
        Head if for the same procedure:
        * No greater binary revision
        * On binary revision equality, no greater resource revision
        """
        return not self.__class__.objects.filter(procedure=self.procedure).filter(
            Q(revision__gt=self.revision)
            | Q(revision=self.revision, resource_revision__gt=self.resource_revision),
        ).exists()

    def can_synchronize_legacy(self):
        # Check if this is the head
        if not self.is_head():
            log.info('do not synchronize %s as not head', self)
            return False
        # Check that resource compilation is successful (or this current task)
        if not self.tasks.filter(key=consts.COMPILE_RESOURCES, state=consts.SUCCESS).exists():
            log.info('do not synchronize %s as no successful resource compilation', self)
            return False
        # Check that compilation is successful for each compiler (or this current task)
        for compiler in Compiler.enabled_objects.all():
            if not self.tasks.filter(key=consts.COMPILE, state=consts.SUCCESS, compiler=compiler).exists():
                log.info('do not synchronize %s as no successful compilation on compiler %s', self, compiler)
                return False
        # Can deploy
        return True

    def __str__(self):
        return '%s@%d/%d' % (self.procedure, self.revision, self.resource_revision)


class Task(models.Model):
    class Meta:
        app_label = 'factory_app' 
        unique_together = (
            ('key', 'procedure_revision', 'compiler'),
        )

    key = models.CharField(max_length=32, choices=consts.TASK_KEY_CHOICES)
    procedure_revision = models.ForeignKey(ProcedureRevision, on_delete=models.CASCADE, related_name='tasks')
    compiler = models.ForeignKey(Compiler, on_delete=models.CASCADE, related_name='tasks', blank=True, null=True)

    state = models.CharField(max_length=32, choices=consts.TASK_STATE_CHOICES, default=consts.PENDING)
    priority = models.IntegerField(choices=consts.PRIORITY_CHOICES, default=consts.NORMAL)

    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(default=None, blank=True, null=True)
    completed_at = models.DateTimeField(default=None, blank=True, null=True)

    output = models.TextField(blank=True)

    def apply_async(self):
        import neoxam.celery
        neoxam.celery
        from neoxam.factory_app import tasks
        tasks.execute_task.apply_async(args=(self.pk,))

    @property
    def name(self):
        return dict(consts.TASK_KEY_CHOICES)[self.key]

    @property
    def total_seconds(self):
        if not self.started_at or not self.completed_at:
            return
        return (self.completed_at - self.started_at).total_seconds

    def reset(self, save=False):
        self.state = consts.PENDING
        self.output = ''
        self.created_at = timezone.now()
        self.started_at = None
        self.completed_at = None
        if save:
            self.save()

    objects = managers.TaskManager()

    def __str__(self):
        return '%s(%d, %s, %s, %s)' % (self.key, self.pk, self.state, self.procedure_revision, self.compiler)


class Batch(models.Model):
    class Meta:
        app_label = 'factory_app'
        
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    procedure_revisions = models.ManyToManyField(ProcedureRevision, related_name='batches')

    def __str__(self):
        return self.name


class CompileLegacyUser(models.Model):
    class Meta:
        app_label = 'factory_app'
        
    username = models.CharField(max_length=32, unique=True)


class CompileLegacyTask(models.Model):
    class Meta:
        app_label = 'factory_app'
        
    created_at = models.DateTimeField(default=timezone.now)
    schema_version = models.PositiveIntegerField()
    procedure_name = models.CharField(max_length=255)
    username = models.CharField(max_length=32)
    state = models.CharField(max_length=32, choices=consts.TASK_STATE_CHOICES, default=consts.RUNNING)
    output = models.TextField(blank=True)
