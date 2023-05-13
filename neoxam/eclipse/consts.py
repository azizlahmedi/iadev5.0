# -*- coding: utf-8 -*-

SVN_TIMEOUT = 30

DIFF_TIMEOUT = 30

COMPILING = 'compiling'
SUCCESS = 'success'
FAILED = 'failed'
STATE_CHOICES = (
    (COMPILING, COMPILING.capitalize()),
    (SUCCESS, SUCCESS.capitalize()),
    (FAILED, FAILED.capitalize()),
)
