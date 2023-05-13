# -*- coding: utf-8 -*-
import os
import subprocess

import neoxam.elastic.backends
from neoxam.eclipse import settings, consts


class SubversionBackend(object):
    def __init__(self, url=settings.SVN_URL, username=settings.SVN_USERNAME, password=settings.SVN_PASSWORD, timeout=consts.SVN_TIMEOUT):
        self.url = url
        self.username = username
        self.password = password
        self.timeout = timeout

    def _svn_command(self, command, *args):
        command = [
            'svn', command,
            '--username', self.username,
            '--password', self.password,
            '--no-auth-cache',
            '--non-interactive',
            '--trust-server-cert',
        ]
        command.extend(args)
        return command

    def _svn_environ(self):
        env = os.environ.copy()
        env['LANG'] = 'en_US.UTF-8'
        return env

    def get_head_revision(self):
        command = self._svn_command('info', self.url)
        output = subprocess.check_output(command, env=self._svn_environ(), stderr=subprocess.DEVNULL,
                                         timeout=self.timeout)
        output = output.decode('utf-8', 'replace')
        try:
            return int(output.split('Revision: ')[1].split('\n')[0])
        except:
            raise ValueError('failed to get head revision from:\n' + output)

    def export(self, revision, root, rel_paths):
        for rel_path in rel_paths:
            path = os.path.join(root, rel_path)
            if not self.export_one(revision, path, rel_path):
                # Temporary fallback mechanism
                if rel_path.startswith('gp2016') and rel_path.split('/')[3] in ('mlg', 'conf',):
                    rel_path = rel_path.replace('gp2016', 'gp2009', 1)
                    self.export_one(revision, path, rel_path)

    def export_one(self, revision, path, rel_path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        command = self._svn_command('export', '--revision', str(revision), '--force', self.url + rel_path, path)
        try:
            subprocess.check_output(command, env=self._svn_environ(), stderr=subprocess.STDOUT,
                                    timeout=self.timeout)
        except subprocess.CalledProcessError as e:
            output = e.output.decode('utf-8')
            if 'E170000' in output:  # Unrecognised URL scheme
                pass
            elif 'E160013' in output:  # Not found
                pass
            else:
                raise
        return os.path.exists(path)


class ElasticBackend(neoxam.elastic.backends.ElasticBackend):
    def get_mapping(self):
        return {
            self.mapping: {
                'properties': {
                    '@timestamp': {'type': 'date'},
                    'external_id': {'type': 'integer'},
                    'action': {'type': 'string', 'index': 'not_analyzed'},
                    'elapsed': {'type': 'integer'},
                    'success': {'type': 'integer'},
                    'exception': {'type': 'string', 'index': 'not_analyzed'},
                    'procedure': {
                        'properties': {
                            'version': {'type': 'integer'},
                            'name': {'type': 'string', 'index': 'not_analyzed'},
                            'name1': {'type': 'string', 'index': 'not_analyzed'},
                            'name2': {'type': 'string', 'index': 'not_analyzed'},
                            'name3': {'type': 'string', 'index': 'not_analyzed'},
                            'name4': {'type': 'string', 'index': 'not_analyzed'},
                            'name5': {'type': 'string', 'index': 'not_analyzed'},
                            'name6': {'type': 'string', 'index': 'not_analyzed'},
                            'name7': {'type': 'string', 'index': 'not_analyzed'},
                            'name8': {'type': 'string', 'index': 'not_analyzed'},
                            'name9': {'type': 'string', 'index': 'not_analyzed'},
                        }
                    },
                    'env': {
                        'properties': {
                            'session': {'type': 'string', 'index': 'not_analyzed'},
                            'hostname': {'type': 'string', 'index': 'not_analyzed'},
                            'username': {'type': 'string', 'index': 'not_analyzed'},
                            'platform_system': {'type': 'string', 'index': 'not_analyzed'},
                            'platform_release': {'type': 'string', 'index': 'not_analyzed'},
                            'platform_version': {'type': 'string', 'index': 'not_analyzed'},
                            'python_version': {'type': 'string', 'index': 'not_analyzed'},
                            'compiler_version': {'type': 'string', 'index': 'not_analyzed'},
                        }
                    },
                }
            }
        }

    def store(self, stats):
        super().store(stats.as_es_doc(), stats.date)


def get_elastic_backend():
    return ElasticBackend(
        settings.ELASTICSEARCH_URL,
        settings.ELASTICSEARCH_INDEX,
        settings.ELASTICSEARCH_MAPPING,
    )
