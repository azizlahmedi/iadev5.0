# -*- coding: utf-8 -*-
import enum
import hashlib
import logging
import os
import shutil
import subprocess
import tempfile

import requests
from django.db.models import Max
from django.utils import timezone
from neoxam.adltrack import models
from neoxam.backport import (consts, models as bp_models)
from neoxam.backport import settings

log = logging.getLogger(__name__)


class Patch:
    def __init__(self,
                return_code,
                patch_content,
                file_pathed,
                to_commit_path):
        self.return_code = return_code
        self.patch_content = patch_content
        self.file_patched = file_pathed
        self.to_commit_path = to_commit_path

class BackportBackend:
    def populate_pool(self, from_version, to_version):
        max_revision = bp_models.Record.objects.filter(from_version=from_version, to_version=to_version).aggregate(
            max_revision=Max('commit__revision')).get('max_revision')
        if max_revision is None:
            max_revision = consts.STARTING_REVISION - 1
        for commit in models.Commit.objects.filter(path__startswith=from_version + '/', revision__gt=max_revision,
                                                   commit_date__lte=timezone.now() - consts.FILTERING_THRESHOLD * 2 ):
            bp_models.Record.objects.get_or_create(commit=commit,
                                                   defaults={'backported': self.is_backported(commit, from_version,
                                                                                              to_version),
                                                             'from_version': from_version, 'to_version': to_version})

    def is_backported(self, commit, from_version, to_version):
        new_path = commit.path.replace(from_version, to_version)
        # if commit is adding a new file, we ignore the commit for backporting
        if not models.Commit.objects.filter(revision__lt=commit.revision, path=commit.path).exists():
            return True
        if not models.Commit.objects.filter(path=new_path).exists():
            return True
        # if it is a java source, it will not be taken into account
        if commit.path.endswith(".java"):
            return True
        if models.Commit.objects.filter(path=new_path,
                                        username=commit.username,
                                        commit_date__gt=(commit.commit_date - consts.FILTERING_THRESHOLD),
                                        commit_date__lt=(commit.commit_date + consts.FILTERING_THRESHOLD)).exists():
            return True
        return False

    def get_commits_without_update(self, from_version, to_version):
        return bp_models.Record.objects.filter(backported=False, from_version=from_version,
                                               to_version=to_version).order_by('-commit__revision')

    def get_commits(self, from_version, to_version):
        self.populate_pool(from_version, to_version)
        return self.get_commits_without_update(from_version, to_version)

    def hide_commit(self, commit, from_version, to_version):
        bp_models.Record.objects.filter(commit=commit, from_version=from_version, to_version=to_version).update(
            backported=True)

    def get_patch(self, commit, to_version):
        from_version = commit.path.split('/')[0]
        from_url = consts.GP_TRUNK_URL + '/' + commit.path + '?revision=' + str(commit.revision)
        from_commit_previous = models.Commit.objects.filter(revision__lt=commit.revision, path=commit.path).order_by(
            '-revision')[:1].get()
        from_url_previous = consts.GP_TRUNK_URL + '/' + from_commit_previous.path + '?revision=' + str(
            from_commit_previous.revision)
        to_commit = models.Commit.objects.filter(path=commit.path.replace(from_version, to_version, 1)).order_by(
            '-revision')[:1].get()
        to_url = consts.GP_TRUNK_URL + '/' + to_commit.path + '?revision=' + str(to_commit.revision)
        returncode, content, file_patched = generate_patch(from_url, from_url_previous, to_url, to_commit_path=to_commit.path)
        patch = Patch(returncode, content.decode("latin-1"), file_patched.decode("latin-1"), to_commit.path)
        return patch


backport_backend = BackportBackend()


class Flag(enum.IntEnum):
    ERROR = -1
    OK = 0
    FUZZY = 1
    CONFLICT = 2


def generate_patch(from_url, from_url_previous, to_url, to_commit_path=None):
    log.info("generate patch between {} and {}, applied to {}".format(from_url,
                                                                      from_url_previous,
                                                                      to_url))
    with tempfile.TemporaryDirectory() as work:
        try:
            from_path = download(from_url, os.path.join(work, 'from.txt'))
            from_previous_path = download(from_url_previous, os.path.join(work, 'from_previous.txt'))
            to_path = download(to_url, os.path.join(work, 'to.txt'))
        except Exception as e:
            return Flag.ERROR, str(e).encode(encoding='latin-1'), "".encode(encoding='latin-1')
        else:
            return _generate_patch(work, from_path, from_previous_path, to_path, to_commit_path)


def _generate_patch(work, from_path, from_previous_path, to_path, to_commit_path=None):
    returncode = Flag.OK
    from_patch_path = os.path.join(work, 'from_patch.txt')
    with open(from_patch_path, 'wb') as fd:
        retcode = subprocess.call(['diff', '-u', from_previous_path, from_path], stdout=fd, cwd=work)
        if retcode not in (0, 1):
            raise ValueError('diff failed')
    to_patch_next = os.path.join(work, 'to_next.txt')
    stdout = subprocess.run(['patch', '-o', to_patch_next, to_path, from_patch_path], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False, cwd=work).stdout
    rej = to_patch_next + '.rej'
    if os.path.isfile(rej):
        return Flag.CONFLICT, "Conflicts occured".encode("latin-1"), "".encode("latin-1")
    if b'hunk ' in stdout.lower():
        returncode = Flag.FUZZY
    to_patch_path = os.path.join(work, 'to_patch.txt')
    with open(to_patch_path, 'wb') as fd:
        retcode = subprocess.call(['diff', '-u', to_path, to_patch_next], stdout=fd, cwd=work)
        if retcode not in (0, 1):
            raise ValueError('diff failed')

    with open(to_patch_path, 'rb') as fd:
        patch_content = fd.read()

    with open(to_patch_next, 'rb') as fd:
        file_patched = fd.read()

    if to_commit_path is not None:
        src_path = os.path.join('/',to_commit_path)
        patch_content = patch_content.replace(to_path.encode('latin-1'), src_path.encode('latin-1'))
        patch_content = patch_content.replace(to_patch_next.encode('latin-1'), src_path.encode('latin-1'))

    return returncode, patch_content, file_patched


def download(url, path):
    bn = hashlib.md5(url.encode('utf-8')).hexdigest()
    cache_path = os.path.join(settings.CACHE_DIR, bn)
    if os.path.exists(cache_path):
        shutil.copy(cache_path, path)
        return path
    response = requests.get(url, auth=(settings.SVN_USERNAME, settings.SVN_PASSWORD), verify=False)
    response.raise_for_status()
    with open(path, 'wb') as fd:
        fd.write(response.content)
    if not os.path.exists(settings.CACHE_DIR):
        os.makedirs(settings.CACHE_DIR)
    shutil.copy(path, cache_path)
    return path
