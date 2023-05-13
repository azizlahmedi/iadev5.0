# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.dblocks import models


@admin.register(models.Lock)
class LockAdmin(admin.ModelAdmin):
    pass
