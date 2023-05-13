# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.webintake import models


@admin.register(models.wUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'ip_address', 'port_number')
