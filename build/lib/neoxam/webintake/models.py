# -*- coding: utf-8 -*-
from django.db import models


class wUser(models.Model):
    user_name = models.CharField(max_length=12, primary_key=True)
    ip_address = models.CharField(max_length=15)
    port_number = models.IntegerField()

    def __str__(self):
        return self.user_name
