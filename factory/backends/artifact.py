# -*- coding: utf-8 -*-
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from distutils.util import get_platform

import requests
from factory import consts
from factory.backends.base import support_environ, unzip, untar


def checksums(path):
    with open(path, mode='rb') as fd:
        content = fd.read()
        return hashlib.md5(content).hexdigest(), hashlib.sha1(content).hexdigest()


class ArtifactBackend(object):
    def __init__(self, user, passwd):
        self.user = user
        self.passwd = passwd

    def put(self, url, path, properties=None):
        if properties:
            url += ';' + ';'.join(['%s=%s' % (k, v) for k, v in properties.items()])
        md5, sha1 = checksums(path)
        headers = {
            'X-Checksum-Md5': md5,
            'X-Checksum-Sha1': sha1,
        }
        with open(path, 'rb') as fd:
            response = requests.put(url, data=fd, auth=(self.user, self.passwd), headers=headers)
            if 400 <= response.status_code < 600:
                raise requests.HTTPError(str(response.status_code) + '\n' + response.text)

    def get(self, url, path):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        d = os.path.dirname(path)
        if not os.path.exists(d):
            os.makedirs(d)
        with open(path, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=128):
                fd.write(chunk)

    def delete(self, url):
        response = requests.delete(url, auth=(self.user, self.passwd))
        if response.status_code in (requests.codes.OK, requests.codes.NOT_FOUND):
            return
        response.raise_for_status()

    def exists(self, url):
        response = requests.head(url, auth=(self.user, self.passwd))
        if response.ok:
            return True
        if response.status_code == requests.codes.NOT_FOUND:
            return False
        response.raise_for_status()


class SourceArtifactBackend(ArtifactBackend):
    def __init__(self, repo_url, user, passwd):
        super(SourceArtifactBackend, self).__init__(user, passwd)
        self.repo_url = repo_url.rstrip('/')

    def artifact_url(self, schema_version, procedure_name, revision):
        return '{repo_url}/{procedure_parts}/{schema_version}/{procedure_basename}-{schema_version}-r{revision}.tgz'.format(
            repo_url=self.repo_url,
            procedure_parts='/'.join(procedure_name.split('.')),
            schema_version=schema_version,
            procedure_basename=procedure_name.replace('.', '_'),
            revision=revision,
        )

    def put(self, schema_version, procedure_name, revision, path):
        properties = {
            'schema.version': schema_version,
            'schema.name': consts.SCHEMA_NAME,
            'procedure.name': procedure_name,
            'revision': revision,
        }
        url = self.artifact_url(schema_version, procedure_name, revision)
        super(SourceArtifactBackend, self).put(url, path, properties)
        return url

    def exists(self, schema_version, procedure_name, revision):
        url = self.artifact_url(schema_version, procedure_name, revision)
        return super(SourceArtifactBackend, self).exists(url)

    def delete(self, schema_version, procedure_name, revision):
        url = self.artifact_url(schema_version, procedure_name, revision)
        return super(SourceArtifactBackend, self).delete(url)

    def get(self, schema_version, procedure_name, revision, path):
        url = self.artifact_url(schema_version, procedure_name, revision)
        super(SourceArtifactBackend, self).get(url, path)

    def extract(self, schema_version, procedure_name, revision, checkout):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, 'src.tgz')
            self.get(schema_version, procedure_name, revision, path)
            if not os.path.exists(checkout):
                os.makedirs(checkout)
            untar(path, checkout)


class BinaryArtifactBackend(ArtifactBackend):
    def __init__(self, repo_url, user, passwd):
        super(BinaryArtifactBackend, self).__init__(user, passwd)
        self.repo_url = repo_url.rstrip('/')

    @property
    def api_url(self):
        base_url, repo_name = self.repo_url.rsplit('/', maxsplit=1)
        return '/'.join([base_url, 'api', 'storage', repo_name])

    def artifact_rel_url(self, schema_version, procedure_name, revision, resource_revision):
        return '{procedure_parts}/{schema_version}/{procedure_basename}-{schema_version}-r{revision}-{resource_revision}.{ext}'.format(
            procedure_parts='/'.join(procedure_name.split('.')),
            schema_version=schema_version,
            procedure_basename=procedure_name.replace('.', '_'),
            revision=revision,
            resource_revision=resource_revision,
            ext=consts.BUNDLE_EXT,
        )

    def artifact_url(self, schema_version, procedure_name, revision, resource_revision):
        return '{repo_url}/{rel_url}'.format(
            repo_url=self.repo_url,
            rel_url=self.artifact_rel_url(schema_version, procedure_name, revision, resource_revision),
        )

    def artifact_api_url(self, schema_version, procedure_name, revision, resource_revision):
        return '{api_url}/{rel_url}'.format(
            api_url=self.api_url,
            rel_url=self.artifact_rel_url(schema_version, procedure_name, revision, resource_revision),
        )

    def update_properties(self, schema_version, procedure_name, revision, resource_revision, properties):
        properties_as_str = '|'.join('%s=%s' % item for item in properties.items())
        data = {'properties': properties_as_str, 'recursive': '0'}
        response = requests.put(
            self.artifact_api_url(schema_version, procedure_name, revision, resource_revision),
            params=data,
            auth=(self.user, self.passwd),
        )
        response.raise_for_status()

    def get_properties(self, schema_version, procedure_name, revision, resource_revision):
        response = requests.get(
            self.artifact_api_url(schema_version, procedure_name, revision, resource_revision) + '?properties',
            auth=(self.user, self.passwd),
        )
        response.raise_for_status()
        return response.json()['properties']

    def put(self, schema_version, procedure_name, revision, resource_revision, path):
        properties = {
            'schema.version': schema_version,
            'schema.name': consts.SCHEMA_NAME,
            'procedure.name': procedure_name,
            'revision': revision,
            'revision.resource': resource_revision,
        }
        url = self.artifact_url(schema_version, procedure_name, revision, resource_revision)
        super(BinaryArtifactBackend, self).put(url, path, properties)
        return url

    def exists(self, schema_version, procedure_name, revision, resource_revision):
        url = self.artifact_url(schema_version, procedure_name, revision, resource_revision)
        return super(BinaryArtifactBackend, self).exists(url)

    def delete(self, schema_version, procedure_name, revision, resource_revision):
        url = self.artifact_url(schema_version, procedure_name, revision, resource_revision)
        return super(BinaryArtifactBackend, self).delete(url)

    def get(self, schema_version, procedure_name, revision, resource_revision, path):
        url = self.artifact_url(schema_version, procedure_name, revision, resource_revision)
        super(BinaryArtifactBackend, self).get(url, path)

    def extract(self, schema_version, procedure_name, revision, resource_revision, app):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, 'src.tgz')
            self.get(schema_version, procedure_name, revision, resource_revision, path)
            if not os.path.exists(app):
                os.makedirs(app)
            unzip(path, app)


class VersionArtifactBackend(ArtifactBackend):
    basename = None

    def __init__(self, repo_url, user, passwd):
        super().__init__(user, passwd)
        self.repo_url = repo_url.rstrip('/')

    def artifact_url(self, version):
        raise NotImplementedError(version)

    @property
    def api_url(self):
        base, repo = self.repo_url.rsplit('/', 1)
        return '%s/api/storage/%s' % (base, repo)

    def exists(self, version):
        url = self.artifact_url(version)
        return super().exists(url)

    def get(self, version, path):
        url = self.artifact_url(version)
        super().get(url, path)

    def get_latest_version(self):
        headers = {'accept': 'application/json'}
        response = requests.get('%s/%s' % (self.api_url, self.basename), headers=headers)
        response.raise_for_status()
        versions = []
        for data in response.json()['children']:
            if data['folder']:
                version_str = data['uri'].strip('/')
                version_spec = [int(p) for p in re.split('\.|p', version_str)]
                versions.append((version_spec, version_str))
        versions.sort(reverse=True, key=lambda x: x[0])
        for version_spec, version_str in versions:
            version_response = requests.get('%s/%s/%s' % (self.api_url, self.basename, version_str), headers=headers)
            version_response.raise_for_status()
            expected = self.artifact_url(version_str).split('/')[-1]
            for version_data in version_response.json()['children']:
                if version_data['uri'].strip('/') == expected:
                    return version_str
        raise ValueError('no %s version available in %s' % (self.basename, self.repo_url))


class CompilerArtifactBackend(VersionArtifactBackend):
    basename = 'deliac-env'

    def artifact_url(self, version):
        return '{repo_url}/{basename}/{version}/{basename}-{version}-{platform}.tar.gz'.format(
            repo_url=self.repo_url,
            basename=self.basename,
            version=version,
            platform=get_platform(),
        )

    def extract(self, version, support_home):
        # Not supposed to exists
        if os.path.exists(support_home):
            raise ValueError('support home already exists: %s' % support_home)
        try:
            with tempfile.TemporaryDirectory() as temp:
                path = os.path.join(temp, 'env.tgz')
                # Download artifact
                self.get(version, path)
                # Create support home
                if not os.path.exists(support_home):
                    os.makedirs(support_home)
                # Uncompress
                untar(path, support_home)
                # Fix paths
                command = [os.path.join(support_home, 'bin', 'fix_path.sh')]
                subprocess.check_output(command, cwd=support_home, stderr=subprocess.STDOUT, timeout=5 * 120)  # do not call with support env
                # Get the version to check if compiler is operational
                command = [os.path.join(support_home, 'bin', 'deliac'), '--version']
                subprocess.check_output(command, cwd=support_home, env=support_environ(support_home), stderr=subprocess.STDOUT, timeout=60)
        except:
            shutil.rmtree(support_home)
            raise
