# -*- coding: utf-8 -*-
import configparser
import logging
import os
import re

import requests
from django.core.management.base import BaseCommand, CommandError

from neoxam.factory_app import consts, models

log = logging.getLogger(__name__)

DEFAULT_VERSION = 2009


class Command(BaseCommand):
    help = 'Asynchronous compile HEADs'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--schema',
            action='store',
            dest='schema_version',
            default=DEFAULT_VERSION,
            type=int,
            help='Schema version (default: %d)' % DEFAULT_VERSION,
        )
        parser.add_argument(
            '-u',
            '--url',
            action='append',
            dest='urls',
            default=None,
            help='Repository url',
        )
        parser.add_argument(
            '-c',
            '--compiler-version',
            action='store',
            default=None,
            dest='compiler_version',
            help='Compiler version',
        )

    def handle(self, *args, **options):
        # Get inputs
        schema_version = options['schema_version']
        urls = options['urls']
        # Check schema version
        if schema_version not in consts.SCHEMA_VERSIONS:
            raise CommandError('invalid schema version: %s' % schema_version)
        # Default repo URLs
        if not urls:
            urls = {
                2009: ['http://iadev-tools/gp/2009', 'http://dotserver.my-nx.com/gp3v4Monoref'],
                2016: ['http://iadev-tools/gp/2016', ],
            }[schema_version]
        procedures = set()
        for url in urls:
            procedures.update(get_procedures_from_url(url))
        for procedure_name, revision, resource_revision in procedures:
            try:
                task = models.Task.objects.get(
                    key=consts.EXPORT_SOURCES,
                    state=consts.SUCCESS,
                    procedure_revision__procedure__schema_version=schema_version,
                    procedure_revision__procedure__name=procedure_name,
                    procedure_revision__revision=revision,
                    procedure_revision__resource_revision=resource_revision,
                )
            except models.Task.DoesNotExist:
                log.error('%d:%s@%d/%d not found' % (schema_version, procedure_name, revision, resource_revision))
            else:
                models.Task.objects.create_compile(task.procedure_revision, self)


def get_procedures_from_url(url):
    procedure_test_basename = 'ihm_menu3'
    url = url.rstrip('/')
    if requests.get(url + '/gp3/%s.gp3' % procedure_test_basename).ok:
        return get_procedures_from_gp3(url)
    if requests.get(url + '/mf/%s.mf' % procedure_test_basename).ok:
        return get_procedures_from_gnx(url)
    raise ValueError('invalid url: %s' % url)


def get_procedures_from_gp3(url):
    procedures = set()
    response = requests.get(url + '/gp3/')
    response.raise_for_status()
    procedures_mf = set(re.findall('[a-z0-9_]+\.gp3', response.text))
    for procedure_mf in list(procedures_mf):
        procedure_name = os.path.splitext(procedure_mf)[0].replace('_', '.')
        response_mf = requests.get(url + '/mf/' + procedure_mf)
        response_mf.raise_for_status()
        config = configparser.ConfigParser()
        config.read_string(response_mf.text)
        revision = config.getint('binary', 'revision')
        resource_revision = config.getint('ressource', 'revision')
        if revision > 0 and resource_revision > 0:
            procedures.add((
                procedure_name,
                revision,
                resource_revision,
            ))
    return procedures


def get_procedures_from_gnx(url):
    procedures = set()
    response = requests.get(url + '/mf/')
    response.raise_for_status()
    procedures_mf = set(re.findall('[a-z0-9_]+\.mf', response.text))
    for procedure_mf in list(procedures_mf):
        procedure_name = os.path.splitext(procedure_mf)[0].replace('_', '.')
        response_mf = requests.get(url + '/mf/' + procedure_mf)
        response_mf.raise_for_status()
        config = configparser.ConfigParser()
        config.read_string(response_mf.text)
        revision = config.getint('revision', 'adl')
        resource_revision = config.getint('revision', 'resource')
        if revision > 0 and resource_revision > 0:
            procedures.add((
                procedure_name,
                revision,
                resource_revision,
            ))
    return procedures
