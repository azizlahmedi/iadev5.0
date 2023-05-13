# -*- coding: utf-8 -*-

PAGINATION = 50

PENDING = 'pending'
COMPILING = 'compiling'
SUCCESS = 'success'
FAILED = 'failed'
STATE_CHOICES = (
    (PENDING, PENDING.capitalize()),
    (COMPILING, COMPILING.capitalize()),
    (SUCCESS, SUCCESS.capitalize()),
    (FAILED, FAILED.capitalize()),
)

LOCK = 'champagne'

FUNCTION = 'function'
FOR_EACH = 'foreach'
SELECT = 'select'
REPORT = 'report'
BRANCH = 'branch'
PATTERN_CHOICES = (
    (FUNCTION, 'Function'),
    (FOR_EACH, 'For Each'),
    (SELECT, 'Select'),
    (REPORT, 'Report'),
    (BRANCH, 'Branch'),
)
