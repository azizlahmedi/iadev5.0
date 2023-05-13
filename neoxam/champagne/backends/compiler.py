# -*- coding: utf-8 -*-
import contextlib
import logging
import os
import subprocess
import tempfile

from neoxam.champagne import settings
from neoxam.champagne.backends import ftp, artifact, magui, telnet, source
from neoxam.versioning import mphash

log = logging.getLogger(__name__)


class CompilerBackend(object):
    def __init__(self, source_backend, ftp_backend, telnet_backend, magui_backend, artifact_backend):
        self.source_backend = source_backend
        self.ftp_backend = ftp_backend
        self.telnet_backend = telnet_backend
        self.magui_backend = magui_backend
        self.artifact_backend = artifact_backend

    def initialize(self):
        self.ftp_backend.initialize()
        self.telnet_backend.initialize()

    def compile(self, procedure_name, procedure_path, app_dir):
        # Outputs
        mag_dir = os.path.join(app_dir, 'mag')
        magui_dir = os.path.join(app_dir, 'magui')
        # Create folders
        os.makedirs(mag_dir, exist_ok=True)
        os.makedirs(magui_dir, exist_ok=True)
        # Naming
        procedure_name = procedure_name.replace('_', '.').lower()
        procedure_basename = procedure_name.replace('.', '_').lower()
        procedure_adl = procedure_basename + '.adl'
        procedure_hash = mphash.mphash(settings.SCHEMA_NAME, procedure_name)
        procedure_mp0 = procedure_hash + '.mp0'
        procedure_me0 = procedure_hash + '.me0'
        schema_mq0 = mphash.mphash(settings.SCHEMA_NAME) + '.mq0'
        # Cleanup
        self.ftp_backend.delete(procedure_mp0)
        # Send procedure
        self.ftp_backend.put(procedure_path, procedure_adl)
        # Compile
        output = self.telnet_backend.compile(procedure_name, procedure_adl, settings.COMPILATION_TIMEOUT)
        # Cleanup
        self.ftp_backend.delete(procedure_me0)
        self.ftp_backend.delete(procedure_adl)
        # Check if MP0 exists
        if not self.ftp_backend.exists(procedure_mp0):
            raise ValueError('failed to generate mp0:\n' + output)
        # Download MP0, MQ0 and DBS
        for basename in (procedure_mp0, schema_mq0, 'magnum.dbs'):
            self.telnet_backend.set_lf(basename)
            self.ftp_backend.get(basename, os.path.join(mag_dir, basename))
        # Cleanup
        self.ftp_backend.delete(procedure_mp0)
        # Create MAGUI
        self.magui_backend.extract(procedure_name, mag_dir, magui_dir)
        # Return the compilation log
        return output

    def compile_and_publish(self, procedure_name, procedure_path, version, patterns):
        # Create work folder
        with tempfile.TemporaryDirectory() as temp:
            # Outputs
            app_dir = os.path.join(temp, 'app')
            src_dir = os.path.join(app_dir, 'src')
            tgz_path = os.path.join(temp, 'artifact.tgz')
            # Create folders
            os.makedirs(src_dir, exist_ok=True)
            # Copy source and apply pattern
            procedure_new_path = self.source_backend.process(procedure_path, procedure_name, src_dir, patterns)
            # Compile
            output = self.compile(procedure_name, procedure_new_path, app_dir)
            # Create tgz
            subprocess.check_call(['tar', '-czf', tgz_path, '.'], cwd=app_dir)
            # Publish
            self.artifact_backend.publish(procedure_name, version, tgz_path)
            # Return logs
            return output

    def close(self):
        for backend in (self.ftp_backend, self.telnet_backend,):
            try:
                backend.close()
            except:
                log.exception('failed to close %s', backend.__class__.__name__)


@contextlib.contextmanager
def compiler_context():
    source_backend = source.SourceBackend()
    ftp_backend = ftp.FTPBackend(
        settings.VMS_HOST,
        settings.VMS_USER,
        settings.VMS_PASSWD,
        settings.VMS_WORK,
    )
    telnet_backend = telnet.TelnetBackend(
        settings.VMS_HOST,
        settings.VMS_USER,
        settings.VMS_PASSWD,
        settings.VMS_WORK,
        settings.TELNET_TIMEOUT,
    )
    magui_backend = magui.MaguiBackend(settings.SUPPORT_HOME)
    artifact_backend = artifact.ArtifactBackend(
        settings.ARTIFACTORY_URL,
        settings.ARTIFACTORY_USER,
        settings.ARTIFACTORY_PASSWD,
    )
    backend = CompilerBackend(source_backend, ftp_backend, telnet_backend, magui_backend, artifact_backend)
    try:
        backend.initialize()
        yield backend
    finally:
        backend.close()
