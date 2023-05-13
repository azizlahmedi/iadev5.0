# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.champagne import models


@admin.register(models.Compilation)
class CompilationAdmin(admin.ModelAdmin):
    date_hierarchy = 'compiled_at'
    list_display = ('compiled_at', 'procedure_name', 'state')
    list_filter = ('state',)
