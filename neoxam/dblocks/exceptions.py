# -*- coding: utf-8 -*-
from django.db import DatabaseError


class LockedError(DatabaseError):
    pass
