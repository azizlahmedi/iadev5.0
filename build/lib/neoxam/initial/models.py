from django.db import models


class InitialCommitRecord(models.Model):
    adlobj_id = models.IntegerField(primary_key=True)

    initial_commit = models.BooleanField()
    version = models.IntegerField()
    svndate = models.DateTimeField(blank=True, null=True)
    user = models.CharField(max_length=256, blank=True, null=True)
    revision = models.IntegerField(blank=True, null=True)
    svn_path = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return "Initial commit: {}, Adlobj id: {}, Version: {}".format(self.initial_commit,
                                                                       self.adlobj_id,
                                                                       self.version)
