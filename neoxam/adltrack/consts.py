# -*- coding: utf-8 -*-
VERSION_CHOICES = (
    (710, 'gp710'),
    (2006, 'gp2006'),
    (2009, 'gp2009'),
)
VERSIONS = [v for v, _ in VERSION_CHOICES]

PAGINATION = 50

REPOSITORY_KEY = 'gp'

COMMIT_LOCK = 'adltrack.commit'
COMPILATION_LOCK = 'adltrack.compilation'

COMPILE_VERSIONS = (2009,)
ANALYZE_VERSIONS = (2006, 2009,)
