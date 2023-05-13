# -*- coding: utf-8 -*-
from django.contrib import admin

from neoxam.scm import models


class CheckoutInline(admin.StackedInline):
    model = models.Checkout
    extra = 0


@admin.register(models.Repository)
class RepositoryAdmin(admin.ModelAdmin):
    inlines = [CheckoutInline, ]
    verbose_name_plural = 'Repositories'

