# -*- coding: utf-8 -*-

SCHEMA_VERSION_CHOICES = (
    (2009, 'gp2009'),
    (2016, 'gp2016'),
)
SCHEMA_VERSIONS = [v for v, _ in SCHEMA_VERSION_CHOICES]

COMPILATION_LOCK = 'factory.compilation'
COMPILATION_LOCK_FOREIGN_ID = 'foreign_id'

EXPORT_SOURCES = 'export_sources'
COMPILE = 'compile'
COMPILE_RESOURCES = 'compile_resources'
SYNCHRONIZE_LEGACY = 'synchronize_legacy'
TECHNICAL_TESTS = 'technical_tests'
TASK_KEY_CHOICES = (
    (EXPORT_SOURCES, 'Export Sources'),
    (COMPILE, 'Compile'),
    (COMPILE_RESOURCES, 'Compile Resources'),
    (SYNCHRONIZE_LEGACY, 'Synchronize Legacy'),
    (TECHNICAL_TESTS, 'Technical Tests')
)

PENDING = 'pending'
RUNNING = 'running'
SUCCESS = 'success'
FAILED = 'failed'
TASK_STATE_CHOICES = (
    (PENDING, PENDING.capitalize()),
    (RUNNING, RUNNING.capitalize()),
    (SUCCESS, SUCCESS.capitalize()),
    (FAILED, FAILED.capitalize()),
)
FINAL_STATES = (SUCCESS, FAILED)

PAGINATION = 50

NORMAL = 0
HIGH = -10
PRIORITY_CHOICES = (
    (NORMAL, 'Normal'),
    (HIGH, 'High'),
)

TASK_EXPIRES = 60  # in seconds

SVN_TIMEOUT = 30
