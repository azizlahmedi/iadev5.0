# -*- coding: utf-8 -*-
from django.contrib import admin
from neoxam.versioning import models


@admin.register(models.AdlObj)
class AdlObjAdmin(admin.ModelAdmin):
    search_fields = ('name', 'revision')
    pass


@admin.register(models.AdlCadre)
class AdlCadreAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Compilation)
class CompilationAdmin(admin.ModelAdmin):
    pass
