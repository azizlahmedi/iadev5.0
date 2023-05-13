# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.delivery import models


@admin.register(models.Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'gp3_url')
