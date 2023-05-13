# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.eclipse import models


@admin.register(models.Stats)
class StatsAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('date', 'action', 'schema_version', 'procedure_name', 'success')
    list_filter = ('action', 'schema_version', 'success')


@admin.register(models.Runtime)
class RuntimeAdmin(admin.ModelAdmin):
    date_hierarchy = 'release_date'
    list_display = ('version', 'enabled', 'release_date', 'url',)
    list_filter = ('enabled',)


@admin.register(models.DeliverTestTask)
class DeliverTestTaskAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ('created_at', 'schema_version', 'procedure_name', 'procedure_test_name', 'state',)
    list_filter = ('schema_version', 'state',)
