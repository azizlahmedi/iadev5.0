# -*- coding: utf-8 -*-
from django.contrib import admin
from neoxam.backport import models

def make_backported(modeladmin, request, queryset):
    queryset.update(backported=True)

def reset_backported(modeladmin, request, queryset):
    queryset.update(backported=False)
    print(queryset)


make_backported.short_description = "Mark selected records as backported"
reset_backported.short_description = "Mark selected records as not yet backported"

@admin.register(models.Record)
class CommitRecordAdmin(admin.ModelAdmin):
    
    search_fields = ('backported', 'commit__revision')

    actions = [make_backported,
               reset_backported]

