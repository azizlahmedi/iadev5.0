# -*- coding: utf-8 -*-
from django import template

register = template.Library()

WEEK = 5 * 8 * 60 * 60  # 5 days of 8 hours each
DAY = 8 * 60 * 60  # 8 hours
HOUR = 60 * 60


@register.filter
def timedelta_humanize(value):
    if isinstance(value, str):
        return value
    data = []
    total_seconds = int(value.total_seconds())
    weeks = total_seconds // WEEK
    days = (total_seconds - weeks * WEEK) // DAY
    hours = (total_seconds - weeks * WEEK - days * DAY) // HOUR
    if weeks:
        data.append('%dw' % weeks)
    if days:
        data.append('%sd' % days)
    if hours:
        data.append('%sh' % hours)
    return ' '.join(data)
