# -*- coding: utf-8 -*-
from django.contrib import admin
from neoxam.gpatcher import models

@admin.register(models.PatchRecord)
class CommitRecordAdmin(admin.ModelAdmin):
    
    search_fields = ('time', 'path')

