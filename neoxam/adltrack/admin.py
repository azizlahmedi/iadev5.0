# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.adltrack import models


@admin.register(models.Commit)
class CommitAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ProcedureVersion)
class ProcedureVersionAdmin(admin.ModelAdmin):
    pass