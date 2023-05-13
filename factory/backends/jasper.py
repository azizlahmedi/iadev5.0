# -*- coding: utf-8 -*-
import logging
import os
import shutil
import tempfile

from factory import consts

log = logging.getLogger(__name__)


class JasperBackend(object):
    def __init__(self, subversion_backend, url):
        super(JasperBackend, self).__init__()
        self.subversion_backend = subversion_backend
        self.url = url

    def get_url(self, schema_version, procedure_name):
        return self.url + '/gp{schema_version}/adl/src/jasper/{procedure_basename}'.format(
            schema_version=schema_version,
            procedure_basename=procedure_name.replace('.', '_'),
        )

    def download(self, schema_version, procedure_name, revision, output_dir):
        # Log
        log.info('download jasper reports for %d:%s@%d', schema_version, procedure_name, revision)
        # Get work folder
        with tempfile.TemporaryDirectory() as temp:
            # Get the configuration path
            path = os.path.join(temp, procedure_name.replace('.', '_'))
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
                    # Output procedure dir
                    output_procedure_dir = os.path.join(output_dir, procedure_name.replace('.', '_'))
                    # Cleanup
                    if os.path.exists(output_procedure_dir):
                        shutil.rmtree(output_procedure_dir)
                    # Copy file
                    shutil.copytree(path, output_procedure_dir)
                    # Fount it, do not continue
                    return
            # No configuration, log it
            log.info('%d:%s has no jasper report', schema_version, procedure_name)
