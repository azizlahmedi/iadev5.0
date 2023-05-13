from django.contrib import admin
from neoxam.initial import models


@admin.register(models.InitialCommitRecord)
class CommitRecordAdmin(admin.ModelAdmin):
    pass
