# -*- coding: utf-8 -*-
import configparser
import datetime
import logging
import os
import shutil

from factory import consts
from factory.backends.base import zip

log = logging.getLogger(__name__)


def safe_set(parser, section, option, value):
    if not parser.has_section(section):
        parser.add_section(section)
    parser.set(section, option, str(value))


class AppBackend(object):
    SECTION_ARTIFACT = 'artifact'
    SECTION_SCHEMA = 'schema'
    SECTION_PROCEDURE = 'procedure'
    SECTION_REVISION = 'revision'
    SECTION_COMPILER = 'compiler'
    SECTION_COMPATIBILITY = 'compatibility'

    def merge(self, remote_app, local_app):
        # Copy all files in local folder in remote folder
        remote_app = os.path.normpath(os.path.abspath(remote_app))
        local_app = os.path.normpath(os.path.abspath(local_app))
        if not os.path.exists(remote_app):
            os.makedirs(remote_app)
        for root, dirs, files in os.walk(local_app):
            for d in dirs:
                d = os.path.join(root, d)
                d = d.replace(local_app, remote_app, 1)
                if not os.path.exists(d):
                    os.makedirs(d)
            for f in files:
                f = os.path.join(root, f)
                new_f = f.replace(local_app, remote_app, 1)
                shutil.copy(f, new_f)

    def clean(self, app, compatibility_versions):
        app_py = os.path.join(app, 'magpy')
        if os.path.isdir(app_py):
            for compatibility_version in os.listdir(app_py):
                if compatibility_version not in compatibility_versions:
                    app_py_version = os.path.join(app_py, compatibility_version)
                    if os.path.isdir(app_py_version):
                        log.info('delete compatibility version %s', compatibility_version)
                        shutil.rmtree(app_py_version)

    def create_or_update_manifest(self, schema_version, procedure_name, revision, resource_revision, app):
        path = os.path.join(app, 'mf', procedure_name.replace('.', '_') + '.mf')
        d = os.path.dirname(path)
        if not os.path.exists(d):
            os.makedirs(d)
        parser = configparser.ConfigParser()
        parser.read(path, encoding='utf-8')
        # Current date
        now = datetime.datetime.utcnow().isoformat()
        # Artifact
        if not parser.has_option(self.SECTION_ARTIFACT, 'created_at'):
            safe_set(parser, self.SECTION_ARTIFACT, 'created_at', now)
        safe_set(parser, self.SECTION_ARTIFACT, 'updated_at', now)
        # Schema
        safe_set(parser, self.SECTION_SCHEMA, 'version', schema_version)
        safe_set(parser, self.SECTION_SCHEMA, 'name', consts.SCHEMA_NAME)
        # Procedure
        safe_set(parser, self.SECTION_PROCEDURE, 'name', procedure_name)
        # Revision
        safe_set(parser, self.SECTION_REVISION, 'adl', revision)
        safe_set(parser, self.SECTION_REVISION, 'resource', resource_revision)
        # Drop compiler section
        parser.remove_section(self.SECTION_COMPILER)
        # Compatibility
        app_py = os.path.join(app, 'magpy')
        compatibility_versions = os.listdir(app_py) if os.path.isdir(app_py) else []
        safe_set(parser, self.SECTION_COMPATIBILITY, 'versions', ', '.join(compatibility_versions))
        # Write back
        with open(path, 'w', encoding='utf-8') as fd:
            parser.write(fd)

    def bundle(self, app, path):
        # Unzip does not respect umask, set rights directly in ZIP files
        for root, dirs, files in os.walk(app):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o775)
            for f in files:
                os.chmod(os.path.join(root, f), 0o664)
        # Create ZIP
        zip(path, app)
