# -*- coding: utf-8 -*-
import os
import subprocess

from neoxam.factory_app import settings, consts


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
