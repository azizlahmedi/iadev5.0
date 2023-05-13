# -*- coding: utf-8 -*-
import configparser
import logging
import os
import shutil
import tempfile

from factory import consts

log = logging.getLogger(__name__)


class ConfigBackend(object):
    SUBVERSION = 'SUBVERSION'
    ARTIFACT = 'ARTIFACT'
    I18N = 'I18N'
    REPOSITORY = 'REPOSITORY'
    COMPILER = 'COMPILER'
    FRAME = 'FRAME'
    LEGACY = 'LEGACY'
    AUTOMATION = 'AUTOMATION'

    def __init__(self, path):
        self.config = configparser.ConfigParser()
        self.config.read(path, encoding='utf-8')

    @property
    def svn_user(self):
        return self.config[self.SUBVERSION]['USER']

    @property
    def svn_passwd(self):
        return self.config[self.SUBVERSION]['PASSWD']

    @property
    def svn_url(self):
        return self.config[self.SUBVERSION]['URL'].rstrip('/')

    @property
    def svn_binary(self):
        return self.config.get(self.SUBVERSION, 'BINARY', fallback='svn')

    @property
    def artifact_user(self):
        return self.config[self.ARTIFACT]['USER']

    @property
    def artifact_passwd(self):
        return self.config[self.ARTIFACT]['PASSWD']

    @property
    def artifact_source_url(self):
        return self.config[self.ARTIFACT]['SOURCE_URL'].rstrip('/')

    @property
    def artifact_binary_url(self):
        return self.config[self.ARTIFACT]['BINARY_URL'].rstrip('/')

    @property
    def artifact_compiler_url(self):
        return self.config[self.ARTIFACT]['COMPILER_URL'].rstrip('/')

    @property
    def i18n_legacy_mo_url(self):
        return self.config[self.I18N]['LEGACY_MO_URL'].rstrip('/')

    @property
    def repo_is_remote(self):
        return self.config.has_option(self.REPOSITORY, 'HOST')

    @property
    def repo_host(self):
        return self.config[self.REPOSITORY]['HOST']

    @property
    def repo_user(self):
        return self.config[self.REPOSITORY]['USER']

    @property
    def repo_passwd(self):
        return self.config[self.REPOSITORY]['PASSWD']

    @property
    def repo_cwd(self):
        return self.config[self.REPOSITORY]['CWD']

    @property
    def compiler_timeout(self):
        return int(self.config[self.COMPILER]['TIMEOUT'])

    @property
    def frame_java_home(self):
        return self.config.get(self.FRAME, 'JAVA_HOME', fallback=os.getenv('JAVA_HOME'))

    @property
    def frame_m2_home(self):
        return self.config.get(self.FRAME, 'M2_HOME', fallback=os.getenv('M2_HOME'))

    @property
    def legacy_vms_host(self):
        return self.config.get(self.LEGACY, 'VMS_HOST', fallback=None)

    @property
    def legacy_vms_user(self):
        return self.config.get(self.LEGACY, 'VMS_USER', fallback=None)

    @property
    def legacy_vms_passwd(self):
        return self.config.get(self.LEGACY, 'VMS_PASSWD', fallback=None)

    @property
    def legacy_unix_host(self):
        return self.config.get(self.LEGACY, 'UNIX_HOST', fallback=None)

    @property
    def legacy_unix_user(self):
        return self.config.get(self.LEGACY, 'UNIX_USER', fallback=None)

    @property
    def legacy_unix_passwd(self):
        return self.config.get(self.LEGACY, 'UNIX_PASSWD', fallback=None)

    @property
    def automation_deliver_url(self):
        return self.config.get(self.AUTOMATION, 'DELIVER_URL', fallback=None)


class ProcedureConfigBackend(object):
    def __init__(self, subversion_backend, url):
        self.subversion_backend = subversion_backend
        self.url = url

    def get_url(self, schema_version, procedure_name):
        return self.url + '/gp{schema_version}/adl/src/conf/{procedure_basename}.conf'.format(
            schema_version=schema_version,
            procedure_basename=procedure_name.replace('.', '_'),
        )

    def download(self, schema_version, procedure_name, revision, output_dir):
        # Log
        log.info('download configuration for %d:%s@%d', schema_version, procedure_name, revision)
        # Get work folder
        with tempfile.TemporaryDirectory() as temp:
            # Get the configuration path
            path = os.path.join(temp, procedure_name.replace('.', '_') + '.conf')
            # Get schema versions where the configuration can be found
            schema_versions = [schema_version]
            schema_versions.extend(consts.FALLBACK_SCHEMA_VERSIONS.get(schema_version, []))
            for schema_version in schema_versions:
                # Get config URL
                url = self.get_url(schema_version, procedure_name)
                # Export
                if self.subversion_backend.safe_export(url, path, revision=revision):
                    # Create folder
                    os.makedirs(output_dir, exist_ok=True)
                    # Copy file
                    shutil.copy(path, os.path.join(output_dir, os.path.basename(path)))
                    # Fount it, do not continue
                    return
            # No configuration, log it
            log.info('%d:%s has no configuration', schema_version, procedure_name)
