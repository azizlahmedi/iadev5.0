# -*- coding: utf-8 -*-
import datetime
import json
import logging

from django.db import models
from django.utils import timezone

log = logging.getLogger(__name__)


class StatsManager(models.Manager):
    def from_request(self, request):
        data = json.loads(request.body)
        timestamp = data['timestamp'] / 1000.0
        date = datetime.datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return super().create(
            date=date,
            action=data['action'],
            schema_version=data['schema_version'],
            procedure_name=data['procedure_name'],
            success=data['success'],
            data=data,
        )
