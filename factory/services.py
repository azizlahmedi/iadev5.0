# -*- coding: utf-8 -*-
import logging
import multiprocessing
import os
import sys
import tempfile

from factory import consts
from factory.backends.app import AppBackend
from factory.backends.artifact import SourceArtifactBackend, BinaryArtifactBackend, CompilerArtifactBackend
from factory.backends.automation import AutomationBackend
from factory.backends.compiler import CompilerBackend
from factory.backends.config import ConfigBackend, ProcedureConfigBackend
from factory.backends.frame import FrameAreaBackend, FrameBackend
from factory.backends.i18n import I18nBackend
from factory.backends.jasper import JasperBackend
from factory.backends.legacy import LegacyBackend
from factory.backends.patch import PatchBackend
from factory.backends.pattern import PatternBackend
from factory.backends.repo import RemoteRepositoryBackend, LocalRepositoryBackend
from factory.backends.scm import SubversionBackend
from factory.backends.source import SourceBackend

log = logging.getLogger(__name__)


class Services(object):
    def __init__(self, source_backend, source_artifact_backend, binary_artifact_backend, compiler_artifact_backend,
                 compiler_backend, i18n_backend, frame_area_backend, frame_backend, app_backend, repo_backend,
                 patch_backend, procedure_config_backend, jasper_backend, legacy_backend, pattern_backend, automation_backend):
        self.source_backend = source_backend
        self.source_artifact_backend = source_artifact_backend
        self.binary_artifact_backend = binary_artifact_backend
        self.compiler_artifact_backend = compiler_artifact_backend
        self.compiler_backend = compiler_backend
        self.i18n_backend = i18n_backend
        self.frame_area_backend = frame_area_backend
        self.frame_backend = frame_backend
        self.app_backend = app_backend
        self.repo_backend = repo_backend
        self.patch_backend = patch_backend
        self.procedure_config_backend = procedure_config_backend
        self.jasper_backend = jasper_backend
        self.legacy_backend = legacy_backend
        self.pattern_backend = pattern_backend
        self.automation_backend = automation_backend

    def ensure_compiler(self, compiler_version, support_home):
        if not os.path.exists(support_home):
            self.compiler_artifact_backend.extract(compiler_version, support_home)
        return self.compiler_backend.get_compatibility_version(support_home, compiler_version)

    def export_sources(self, schema_version, procedure_name, revision):
        # Log
        log.info('export sources of %d:%s@%d', schema_version, procedure_name, revision)
        # Check if artifact already exist
        if not self.source_artifact_backend.exists(schema_version, procedure_name, revision):
            # If not, create and push it
            with tempfile.TemporaryDirectory() as temp:
                path = os.path.join(temp, 'current.tgz')
                self.source_backend.create_tgz(schema_version, procedure_name, revision, path)
                self.source_artifact_backend.put(schema_version, procedure_name, revision, path)
        # Return its URL
        return self.source_artifact_backend.artifact_url(schema_version, procedure_name, revision)

    def compile(self, schema_version, procedure_name, revision, compiler_version, support_home, app):
        # Log
        log.info('compile %d:%s@%d with version %s', schema_version, procedure_name, revision, compiler_version)
        # Get work folder
        with tempfile.TemporaryDirectory() as checkout:
            # Get the ADL source code and fix its frames and sources
            self.source_artifact_backend.extract(schema_version, procedure_name, revision, checkout)
            self.patch_backend.fix(schema_version, procedure_name, revision, checkout, compiler_version)
            self.frame_area_backend.fix(schema_version, procedure_name, revision, checkout)
            # Get compatibility version
            compatibility_version = self.compiler_backend.get_compatibility_version(support_home, compiler_version)
            # Compile ADL
            output = self.compiler_backend.compile(support_home, compiler_version, checkout, schema_version, procedure_name, revision, os.path.join(app, 'magpy', compatibility_version))
            # Return the compilation output
            return output

    def compile_resources(self, schema_version, procedure_name, frame_revision, i18n_revision, config_revision, jasper_revision, app):
        # Log
        log.info('compile %d:%s resources (frames @%s, i18n @%s)', schema_version, procedure_name, frame_revision, i18n_revision)
        # Get the legacy .mo
        self.i18n_backend.download_all_legacy_mo(schema_version, procedure_name, os.path.join(app, 'mlg'))
        # Generate the Delia .mo
        all_mo = self.i18n_backend.download_and_compile_all_po(schema_version, procedure_name, os.path.join(app, 'mo'), i18n_revision)
        # Compile the Java frames
        self.frame_backend.generate_and_compile(schema_version, procedure_name, frame_revision, all_mo, os.path.join(app, 'java'))
        # Get the procedure configuration
        self.procedure_config_backend.download(schema_version, procedure_name, config_revision, os.path.join(app, 'conf'))
        # Get the procedure Jasper files
        self.jasper_backend.download(schema_version, procedure_name, jasper_revision, os.path.join(app, 'jasper'))

    def synchronize(self, schema_version, procedure_name, revision, resource_revision, app, compatibility_versions=None):
        # Log
        log.info('synchronize %d:%s@%s/%s', schema_version, procedure_name, revision, resource_revision)
        # Get work folder
        with tempfile.TemporaryDirectory() as temp:
            # Get the content of the remote APP
            remote_app = os.path.join(temp, 'app')
            if self.binary_artifact_backend.exists(schema_version, procedure_name, revision, resource_revision):
                self.binary_artifact_backend.extract(schema_version, procedure_name, revision, resource_revision, remote_app)
            # Get the artifact path
            path = os.path.join(temp, 'current.' + consts.BUNDLE_EXT)
            # Merge
            self.app_backend.merge(remote_app, app)
            # If compatibility versions is specified, clean deprecated versions
            if compatibility_versions is not None:
                self.app_backend.clean(remote_app, compatibility_versions)
            # Create or update manifest
            self.app_backend.create_or_update_manifest(schema_version, procedure_name, revision, resource_revision, remote_app)
            # Create the bundle
            self.app_backend.bundle(remote_app, path)
            # Put back the new content
            self.binary_artifact_backend.put(schema_version, procedure_name, revision, resource_revision, path)

    def synchronize_legacy(self, schema_version, procedure_name, revision, resource_revision):
        # Log
        log.info('synchronize %d:%s@%s/%s with legacy', schema_version, procedure_name, revision, resource_revision)
        # Create a work folder
        with tempfile.TemporaryDirectory() as temp:
            # Get the artifact path
            path = os.path.join(temp, 'current.' + consts.BUNDLE_EXT)
            # Download it
            self.binary_artifact_backend.get(schema_version, procedure_name, revision, resource_revision, path)
            # Create a connection
            with self.repo_backend.connection():
                # Synchronize
                self.repo_backend.synchronize(schema_version, procedure_name, path)

    def compile_legacy(self, schema_version, procedure_name, compiler_homes):
        # Log
        log.info('compile legacy %d:%s', schema_version, procedure_name)
        # Create a work folder
        with tempfile.TemporaryDirectory() as work:
            # Copy revision
            revision = resource_revision = -1
            # Get the ADL source code and fix its frames and sources
            project_path = self.source_backend.export_project(schema_version, work, 'HEAD')
            self.legacy_backend.get_sources(project_path, procedure_name)
            self.patch_backend.fix(schema_version, procedure_name, sys.maxsize, work, min(compiler_homes.keys()))
            self.frame_area_backend.fix_local(schema_version, procedure_name, work)
            # App
            with tempfile.TemporaryDirectory() as app:
                # Compilation processes
                all_process = []
                # Compile ADL
                for compiler_version, support_home in compiler_homes.items():
                    compatibility_version = self.compiler_backend.get_compatibility_version(support_home, compiler_version)
                    process = multiprocessing.Process(
                        target=self.compiler_backend.compile,
                        args=(
                            support_home,
                            compiler_version,
                            work,
                            schema_version,
                            procedure_name,
                            revision,
                            os.path.join(app, 'magpy', compatibility_version),
                        )
                    )
                    process.start()
                    all_process.append(process)
                # I18n
                all_mo = self.i18n_backend.compile_all_po(
                    procedure_name,
                    os.path.join(work, 'gp%d' % schema_version, 'adl', 'src', 'mlg'),
                    os.path.join(app, 'mo'),
                )
                # Compile Java
                self.frame_backend.generate_and_compile_local(schema_version, procedure_name, all_mo, work, os.path.join(app, 'java'), compile_legacy=False)
                # Join sub-processed
                for process in all_process:
                    process.join(timeout=self.compiler_backend.timeout)
                    if process.exitcode != 0:
                        raise ValueError('delia compilation failed')
                # Create manifest
                self.app_backend.create_or_update_manifest(schema_version, procedure_name, revision, resource_revision, app)
                # Create and publish artifacts
                with tempfile.TemporaryDirectory() as temp:
                    # Get bundle path
                    path = os.path.join(temp, 'current.' + consts.BUNDLE_EXT)
                    # Create bundle
                    self.app_backend.bundle(app, path)
                    # Synchronize
                    with self.repo_backend.connection():
                        self.repo_backend.synchronize(schema_version, procedure_name, path)

    def technical_tests(self, schema_version, procedure_name, revision, resource_revision, sandbox=False):
        # Log
        log.info('technical tests on %d:%s@%d', schema_version, procedure_name, revision)
        # Get work folder
        with tempfile.TemporaryDirectory() as checkout:
            # Get the ADL source
            self.source_artifact_backend.extract(schema_version, procedure_name, revision, checkout)
            # Run technical tests
            technical_tests = self.pattern_backend.run_technical_tests(checkout, schema_version, procedure_name, skip_on_annotate_error=False, sandbox=sandbox)
            # Compute the properties
            properties = dict(('tests.tech.%s' % tt.key, tt.result_as_str) for tt in technical_tests)
            # Update properties
            self.binary_artifact_backend.update_properties(schema_version, procedure_name, revision, resource_revision, properties)
            # Get the binary URL
            url = self.binary_artifact_backend.artifact_url(schema_version, procedure_name, revision, resource_revision)
            # Ask for delivery
            self.automation_backend.deliver(schema_version, procedure_name, revision, resource_revision, url, technical_tests)


def create_services(config_path):
    config_backend = ConfigBackend(config_path)
    subversion_backend = SubversionBackend(
        config_backend.svn_user, config_backend.svn_passwd,
        config_backend.svn_binary,
    )
    source_backend = SourceBackend(
        subversion_backend,
        config_backend.svn_url,
    )
    source_artifact_backend = SourceArtifactBackend(
        config_backend.artifact_source_url,
        config_backend.artifact_user,
        config_backend.artifact_passwd,
    )
    binary_artifact_backend = BinaryArtifactBackend(
        config_backend.artifact_binary_url,
        config_backend.artifact_user,
        config_backend.artifact_passwd,
    )
    compiler_artifact_backend = CompilerArtifactBackend(
        config_backend.artifact_compiler_url,
        config_backend.artifact_user,
        config_backend.artifact_passwd,
    )
    compiler_backend = CompilerBackend(config_backend.compiler_timeout)
    i18n_backend = I18nBackend(
        subversion_backend, config_backend.svn_url,
        config_backend.i18n_legacy_mo_url,
        consts.LANGUAGES,
    )
    frame_area_backend = FrameAreaBackend(subversion_backend, config_backend.svn_url)
    frame_backend = FrameBackend(
        subversion_backend,
        config_backend.svn_url,
        config_backend.frame_java_home,
        config_backend.frame_m2_home,
    )
    app_backend = AppBackend()
    if config_backend.repo_is_remote:
        repo_backend = RemoteRepositoryBackend(
            config_backend.repo_host,
            config_backend.repo_user,
            config_backend.repo_passwd,
            config_backend.repo_cwd,
        )
    else:
        repo_backend = LocalRepositoryBackend(config_backend.repo_cwd)
    patch_backend = PatchBackend()
    procedure_config_backend = ProcedureConfigBackend(
        subversion_backend,
        config_backend.svn_url,
    )
    jasper_backend = JasperBackend(
        subversion_backend,
        config_backend.svn_url,
    )
    legacy_backend = LegacyBackend(
        config_backend.legacy_vms_host,
        config_backend.legacy_vms_user,
        config_backend.legacy_vms_passwd,
        config_backend.legacy_unix_host,
        config_backend.legacy_unix_user,
        config_backend.legacy_unix_passwd,
    )
    pattern_backend = PatternBackend(compiler_backend)
    automation_backend = AutomationBackend(config_backend.automation_deliver_url)
    return Services(
        source_backend,
        source_artifact_backend,
        binary_artifact_backend,
        compiler_artifact_backend,
        compiler_backend,
        i18n_backend,
        frame_area_backend,
        frame_backend,
        app_backend,
        repo_backend,
        patch_backend,
        procedure_config_backend,
        jasper_backend,
        legacy_backend,
        pattern_backend,
        automation_backend,
    )
