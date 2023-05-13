# -*- coding: utf-8 -*-
import os
import socket

from django.db import models

from neoxam.scm import consts, settings


class Repository(models.Model):
    class Meta:
        unique_together = (
            ('scm', 'url'),
        )

    key = models.CharField(max_length=32, unique=True)
    scm = models.CharField(max_length=16, choices=consts.SCM_CHOICES, default=consts.SUBVERSION)
    url = models.URLField()
    timeout = models.PositiveIntegerField()

    def __str__(self):
        return self.key


class Checkout(models.Model):
    hostname = models.CharField(max_length=64, default=socket.gethostname)
    repository = models.ForeignKey(Repository,on_delete=models.CASCADE, related_name='checkouts')
    in_use = models.BooleanField(default=False)

    @property
    def basename(self):
        return self.repository.key + '_' + str(self.pk)

    @property
    def root(self):
        return os.path.join(settings.CHECKOUT_DIR, self.basename)

    def __str__(self):
        return '%s %d @ %s' % (self.repository.key, self.pk, self.hostname)
