# -*- coding: utf-8 -*-
import contextlib
import logging
import os
import shutil
import uuid

import paramiko

from factory import consts
from factory.backends.base import unzip

log = logging.getLogger(__name__)


class RepositoryBackend(object):
    def synchronize(self, schema_version, procedure_name, path):
        raise NotImplementedError('synchronize')

    @contextlib.contextmanager
    def connection(self):
        yield self


class RemoteRepositoryBackend(object):
    def __init__(self, host, user, passwd, cwd, timeout=2 * 60, banner_timeout=2 * 60, command_timeout=3 * 60,
                 sftp_timeout=3 * 60):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.cwd = cwd
        self.cx = None
        self.sftp = None
        self.timeout = timeout
        self.banner_timeout = banner_timeout
        self.command_timeout = command_timeout
        self.sftp_timeout = sftp_timeout

    @contextlib.contextmanager
    def connection(self):
        try:
            self.initialize()
            yield self
        finally:
            try:
                self.close()
            except:
                log.expection('failed to close SSH connection')

    def __str__(self):
        return '%s@%s:%s' % (self.user, self.host, self.cwd)

    def initialize(self):
        log.info('connect on %s', self)
        self.cx = paramiko.SSHClient()
        self.cx.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.cx.connect(self.host, username=self.user, password=self.passwd, timeout=self.timeout,
                        banner_timeout=self.banner_timeout)
        self.sftp = self.cx.open_sftp()
        self.sftp.get_channel().settimeout(self.sftp_timeout)

    def close(self):
        log.info('disconnect from %s', self)
        cx = self.cx
        self.cx = None
        self.sftp = None
        cx.close()

    def check_call(self, command):
        log.info('execute command: %s', command)
        fd_stdin, fd_stdout, fd_stderr = self.cx.exec_command(command, timeout=self.command_timeout)
        stderr = fd_stderr.read().decode('utf-8', 'replace')
        if stderr != '':
            raise ValueError('"%s" command failed:\n%s' % (command, stderr))
        return fd_stdout.read().decode('utf-8', 'replace')

    def synchronize(self, schema_version, procedure_name, path):
        log.info('synchronize %d:%s with %s', schema_version, procedure_name, self)
        app = os.path.join(self.cwd, str(schema_version))
        remote_dir = os.path.join(app, consts.BUNDLE_EXT)
        remote_path = os.path.join(remote_dir, '%s.%s' % (procedure_name.replace('.', '_'), consts.BUNDLE_EXT))
        remote_tmp_path = '.' + str(uuid.uuid4())
        for name in (app, remote_dir):
            try:
                self.sftp.stat(name)
            except IOError:
                self.check_call('mkdir -p {name} && chmod 775 {name}'.format(name=name))
        self.sftp.put(path, remote_tmp_path)
        try:
            command = 'cp {remote_tmp_path} {remote_path} && chmod 664 {remote_path} && unzip -o {remote_path} -d {app}'.format(
                app=app,
                remote_path=remote_path,
                remote_tmp_path=remote_tmp_path,
            )
            self.check_call(command)
        finally:
            self.sftp.remove(remote_tmp_path)


class LocalRepositoryBackend(RepositoryBackend):
    def __init__(self, cwd):
        self.cwd = cwd

    def synchronize(self, schema_version, procedure_name, path):
        app = os.path.join(self.cwd, str(schema_version))
        app_gnx = os.path.join(app, consts.BUNDLE_EXT)
        os.makedirs(app_gnx, exist_ok=True)
        gnx_path = os.path.join(app_gnx, '%s.%s' % (procedure_name.replace('.', '_'), consts.BUNDLE_EXT))
        shutil.copy(path, gnx_path)
        unzip(gnx_path, app)
