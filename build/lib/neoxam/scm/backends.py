# -*- coding: utf-8 -*-
import contextlib
import logging
import os
import shutil
import socket
import subprocess

from django.db import transaction
from neoxam.scm import models

log = logging.getLogger(__name__)


class RepositoryBackend(object):
    @contextlib.contextmanager
    def checkout_context(self, key):
        hostname = socket.gethostname()
        with transaction.atomic():
            log.info('lock repository %s', key)
            repository = models.Repository.objects.select_for_update().get(key=key)
            log.info('repository %s locked', repository)
            try:
                checkout = repository.checkouts.filter(hostname=hostname, in_use=False).order_by('?')[:1].get()
            except models.Checkout.DoesNotExist:
                checkout = repository.checkouts.create(hostname=hostname, in_use=True)
            else:
                checkout.in_use = True
                checkout.save(update_fields=('in_use',))
            log.info('unlock repository %s', repository)
        try:
            yield SubversionBackend(checkout)
        finally:
            checkout.in_use = False
            checkout.save(update_fields=('in_use',))


class CheckoutBackend(object):
    def __init__(self, database_checkout):
        self.database_checkout = database_checkout

    @property
    def root(self):
        return self.database_checkout.root

    def checkout(self, revision=None):
        raise NotImplementedError()


def get_svn_environ():
    env = os.environ.copy()
    env['LANG'] = 'en_US.utf8'
    return env


class SubversionBackend(CheckoutBackend):
    def __init__(self, database_checkout):
        super(SubversionBackend, self).__init__(database_checkout)

    def _get_revision(self, revision=None):
        return int(self.get_info_key('Revision', revision=revision))

    def get_head_revision(self):
        return self._get_revision('HEAD')

    def get_revision(self):
        return self._get_revision()

    def get_url(self):
        return self.get_info_key('URL')

    def get_info_key(self, key, revision=None):
        data, output = self.info(revision=revision)
        if key not in data:
            raise ValueError('%s not found in:\n%s' % (key, output))
        return data[key]

    def checkout(self, revision=None):
        repository_url = self.database_checkout.repository.url.rstrip('/')
        if os.path.isfile(self.root):
            raise NotImplementedError('file not expected: %s' % self.root)
        if os.path.exists(self.root):
            checkout_url = self.get_url()
            if checkout_url != repository_url:
                log.warning('delete checkout, url mismatch: %s (checkout) != %s (database)', checkout_url, repository_url)
                shutil.rmtree(self.root)
        command = ['svn']
        if not os.path.exists(self.root):
            command.append('checkout')
            if revision:
                command.extend(['-r', str(revision)])
            command.extend([repository_url, self.root])
        else:
            command.append('update')
            if revision:
                command.extend(['-r', str(revision)])
            command.append(self.root)
        try:
            subprocess.check_output(
                command,
                timeout=self.database_checkout.repository.timeout,
                stderr=subprocess.STDOUT,
                env=get_svn_environ(),
            )
        except:
            shutil.rmtree(self.root)
            raise

    def info(self, revision=None):
        command = ['svn', 'info', ]
        if revision:
            command.extend(['-r', str(revision)])
        output = subprocess.check_output(command, timeout=20, cwd=self.root, stderr=subprocess.STDOUT,
                                         env=get_svn_environ())
        output = output.decode('latin1', errors='replace')
        data = {}
        for line in output.split('\n'):
            args = line.split(': ', 1)
            if len(args) == 2:
                data[args[0].strip()] = args[1].strip()
        return data, output


repository_backend = RepositoryBackend()
