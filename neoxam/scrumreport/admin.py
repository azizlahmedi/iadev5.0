from django.contrib import admin

# Register your models here.
from .models import Project, Scrum, Sprint, Issue, NxUser

admin.site.register(Project)
admin.site.register(Scrum)
admin.site.register(Sprint)
admin.site.register(Issue)
admin.site.register(NxUser)
