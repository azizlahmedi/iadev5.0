from django.db import models

class PatchRecord(models.Model):

    time = models.DateTimeField()

    version = models.CharField(max_length=32)

    path = models.CharField(max_length=256)

    status = models.BooleanField()

    ip = models.CharField(max_length=32)

    def __str__(self):
        return "{time}, {version}, {path}, {status}, {ip}".format(time=self.time,
                                                                  version=self.version,
                                                          path=self.path,
                                                          status=self.status,
                                                          ip=self.ip)
