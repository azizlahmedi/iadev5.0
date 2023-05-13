# -*- coding: utf-8 -*-
import os
import re
import tarfile
import zipfile

import delia_commons
from delia_commons.singleton import Singleton


def delia_context():
    """Ensure that do not re-use initialized context"""
    Singleton.reset(delia_commons.Context)
    ctx = delia_commons.Context()
    return ctx


def get_project_path(checkout, schema_version):
    return os.path.join(checkout, 'gp%d' % schema_version)


def support_environ(support_home):
    env = os.environ.copy()
    env.pop('VIRTUAL_ENV', None)
    env.pop('PYTHONPATH', None)
    libs = os.path.join(support_home, 'lib')
    if 'LD_LIBRARY_PATH' in env:
        libs += os.pathsep + env['LD_LIBRARY_PATH']
    bins = os.path.join(support_home, 'bin')
    if 'PATH' in env:
        bins += os.pathsep + env['PATH']
    env.update({
        'PYTHONHOME': support_home,
        'LANG': 'en_US.UTF-8',
        'LD_LIBRARY_PATH': libs,
        'PATH': bins,
    })
    return env


def unzip(path, output):
    with zipfile.ZipFile(path, 'r') as fd:
        fd.extractall(output)


def untar(path, output):
    with tarfile.open(path) as fd:
        fd.extractall(output)


def tar(path, root):
    with tarfile.open(path, 'w:gz') as fd:
        for bn in os.listdir(root):
            fd.add(os.path.join(root, bn), arcname=bn)


def zip(path, root):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as fd:
        for arcname in os.listdir(root):
            add_to_zip(fd, os.path.join(root, arcname), arcname)


def add_to_zip(fd, path, arcname):
    fd.write(path, arcname)
    if os.path.isdir(path):
        for bn in os.listdir(path):
            add_to_zip(fd, os.path.join(path, bn), os.path.join(arcname, bn))


def compiler_lt(compiler_version, requirement):
    def parse(v):
        return [int(p) for p in re.search('(\d+(\.\d+)*)', v).group(0).split('.')]

    return parse(compiler_version) < parse(requirement)


class TechnicalTest(object):
    def __init__(self, key, success, log):
        self.key = key
        self.success = success
        self.log = log

    @property
    def result_as_str(self):
        return 'pass' if self.success else 'fail'
