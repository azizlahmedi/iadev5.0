# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.factory_app import models


@admin.register(models.Compiler)
class CompilerAdmin(admin.ModelAdmin):
    list_display = ('version', 'compatibility_version', 'enabled',)
    list_filter = ('enabled',)
    ordering = ('-version',)


@admin.register(models.Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ('schema_version', 'name',)
    list_filter = ('schema_version',)
    ordering = ('-schema_version', 'name',)


@admin.register(models.ProcedureRevision)
class ProcedureRevisionAdmin(admin.ModelAdmin):
    list_display = ('procedure', 'revision', 'resource_revision',)
    list_filter = ('procedure__schema_version',)
    ordering = ('-revision', '-resource_revision',)


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('key', 'procedure_revision', 'compiler', 'created_at', 'priority', 'state',)
    list_filter = ('key', 'state', 'priority',)


@admin.register(models.Batch)
class BatchAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('created_at', 'name',)
    readonly_fields = ('procedure_revisions',)


@admin.register(models.CompileLegacyUser)
class CompileLegacyUserAdmin(admin.ModelAdmin):
    list_display = ('username',)


@admin.register(models.CompileLegacyTask)
class CompileLegacyTaskAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('created_at', 'schema_version', 'procedure_name', 'state',)
    list_filter = ('schema_version', 'state',)
