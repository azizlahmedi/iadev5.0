# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.harry import models


@admin.register(models.Push)
class PushAdmin(admin.ModelAdmin):
    date_hierarchy = 'creation_date'
    list_display = ('hostname', 'procedure_name', 'creation_date')
    list_filter = ('hostname',)


@admin.register(models.JsonUntranslated)
class JsonUntranslatedAdmin(admin.ModelAdmin):
    date_hierarchy = 'creation_date'
    list_display = ('creation_date', 'username', 'comment')
