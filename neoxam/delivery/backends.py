# -*- coding: utf-8 -*-
import configparser
import logging
import os
import subprocess
import tempfile
import zipfile

import requests

from neoxam.factory_app.models import Compiler

log = logging.getLogger(__name__)


def read_mf(path, entry):
    with zipfile.ZipFile(path) as gnx_fd:
        content = gnx_fd.read(entry).decode('utf-8')
        config = configparser.ConfigParser()
        config.read_string(content)
        return config


class DeliveryBackend(object):
    def create_delivery(self, tar_gz_path, repository, procedure_names):
        errors = []
        with tempfile.TemporaryDirectory() as temp:
            for procedure_name in procedure_names:
                procedure_basename = procedure_name.replace('.', '_').lower()
                gp3_url = repository.gp3_url.rstrip('/') + '/' + procedure_basename + '.gp3'
                response = requests.get(gp3_url, stream=True)
                if response.status_code != 200:
                    errors.append('%s .gp3 does not exist (%s %d)' % (procedure_name, gp3_url, response.status_code))
                else:
                    gp3_path = os.path.join(temp, procedure_basename + '.gp3')
                    with open(gp3_path, 'wb') as fd:
                        for chunk in response.iter_content(chunk_size=128):
                            fd.write(chunk)
                    try:
                        gp3_config = read_mf(gp3_path, 'META-INF/MANIFEST.MF')
                    except zipfile.BadZipfile:
                        errors.append('%s .gp3 is corrupted' % procedure_name)
                    else:
                        gp3_procedure_name = gp3_config.get('gp3', 'procedure')
                        gp3_schema_version = gp3_config.get('gp3', 'version')
                        gp3_revision = int(gp3_config.get('binary', 'revision'))
                        gp3_resource_revision = int(gp3_config.get('ressource', 'revision'))
                        if gp3_revision <= 0 or gp3_resource_revision <= 0:
                            errors.append('%s is not under SVN (%d:%d)' % (procedure_name, gp3_revision, gp3_resource_revision))
                        elif procedure_name != gp3_procedure_name:
                            log.error('procedure name mismatch: %s (expected) != %s (found)', procedure_name, gp3_procedure_name)
                        else:
                            gnx_path = os.path.join(temp, procedure_basename + '.gnx')
                            gnx_url = 'http://nx-artifacts:8085/artifactory/gp3-adl-binaries/{procedure_path}/{schema_version}/{procedure_basename}-{schema_version}-r{revision}-{resource_revision}.gnx'.format(
                                procedure_path=procedure_name.replace('.', '/'),
                                procedure_basename=procedure_basename,
                                schema_version=gp3_schema_version,
                                revision=gp3_revision,
                                resource_revision=gp3_resource_revision,
                            )
                            response = requests.get(gnx_url, stream=True)
                            if response.status_code != 200:
                                errors.append('%s .gnx does not exist (%s %d)' % (procedure_name, gnx_url, response.status_code))
                            else:
                                with open(gnx_path, 'wb') as fd:
                                    for chunk in response.iter_content(chunk_size=128):
                                        fd.write(chunk)
                                try:
                                    with zipfile.ZipFile(gnx_path) as gnx_fd:
                                        namelist = gnx_fd.namelist()
                                        if 'mo/en/%s_en.mo' % procedure_basename not in namelist:
                                            errors.append('%s resources are not in .gnx' % procedure_name)
                                        for compiler in Compiler.enabled_objects.all():
                                            if 'magpy/%s/%s.py' % (compiler.version, procedure_basename) not in namelist:
                                                errors.append('%s .py of compiler %s is missing' % (procedure_name, compiler.version))
                                except zipfile.BadZipfile:
                                    errors.append('%s .gnx is corrupted' % procedure_name)
            if not errors:
                os.makedirs(os.path.dirname(tar_gz_path), exist_ok=True)
                subprocess.check_call(['tar', '-zcf', tar_gz_path, ] + os.listdir(temp), cwd=temp)
        return errors
