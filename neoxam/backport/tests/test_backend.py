# -*- coding: utf-8 -*-
import neoxam.tests

neoxam.tests.setup()
import datetime
import unittest

from django.test import TransactionTestCase

from neoxam.adltrack import models
from neoxam.backport import models as bp_models
from neoxam.backport.backends import backport_backend
from neoxam.backport import consts
from unittest.mock import MagicMock
from django.utils import timezone
from django.shortcuts import get_object_or_404


class MyDatetime(datetime.datetime):
    @classmethod
    def now(cls):
        return datetime.datetime(2016, 1, 2, 12, 24, tzinfo=timezone.utc)


class TestGetcommits(TransactionTestCase):
    def setUp(self):
        self.tmp_filtering_threshold = consts.FILTERING_THRESHOLD
        self.tmp_starting_revision = consts.STARTING_REVISION
        consts.FILTERING_THRESHOLD = datetime.timedelta(hours=72)
        consts.STARTING_REVISION = 1
        backport_backend.get_patch = MagicMock(return_value=None)
        TransactionTestCase.setUp(self)

    def tearDown(self):
        consts.FILTERING_THRESHOLD = self.tmp_filtering_threshold
        consts.STARTING_REVISION = self.tmp_starting_revision
        TransactionTestCase.tearDown(self)

    def test_new_version_exists(self):
        models.Commit.objects.create(
            revision=9,
            path='gp2006/bin/bibtoto.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 9, 4, 16, 0, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=10,
            path='gp2006/bin/bibtoto.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 10, 4, 16, 0, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=11,
            path='gp2009/bin/bibtoto.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 10, 4, 16, 0, tzinfo=timezone.utc))
        commits = backport_backend.get_commits('gp2006', 'gp2009')
        self.assertEquals(0, len(commits))

    def test_new_version_not_exists(self):
        # patch will be generated only for the existing source files
        models.Commit.objects.create(
            revision=9,
            path='gp2006/bin/bibtoto.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 9, 4, 16, 0, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=10,
            path='gp2006/bin/bibtoto.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 10, 4, 16, 0, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=4,
            path='gp2009/bin/bibtoto.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 6, 12, 24, tzinfo=timezone.utc))
        commits = backport_backend.get_commits('gp2006', 'gp2009')
        self.assertEquals(1, len(commits))

    def test_revision_too_old(self):
        consts.STARTING_REVISION = 100
        models.Commit.objects.create(
            revision=9,
            path='gp2006/bin/bibtoto.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 9, 4, 16, 0, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=10,
            path='gp2006/bin/bibtoto.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 10, 4, 16, 0, tzinfo=timezone.utc))
        commits = backport_backend.get_commits('gp2006', 'gp2009')
        self.assertEquals(0, len(commits))

    def test_backport_too_late(self):
        # patch will be generated only for the existing source files
        models.Commit.objects.create(
            revision=147116,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 10, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147117,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 12, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147122,
            path='gp2009/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 6, 12, 24, tzinfo=timezone.utc))
        commits = backport_backend.get_commits('gp2006', 'gp2009')
        self.assertEquals(1, len(commits))

    def test_backport_too_early_to_check(self):
        backup = datetime.datetime
        try:
            datetime.datetime = MyDatetime
            models.Commit.objects.create(
                revision=147116,
                path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
                username='hhu',
                commit_date=datetime.datetime(2016, 1, 1, 10, 24, tzinfo=timezone.utc))
            models.Commit.objects.create(
                revision=147117,
                path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
                username='hhu',
                commit_date=datetime.datetime(2016, 1, 1, 12, 24, tzinfo=timezone.utc))
            commits = backport_backend.get_commits('gp2006', 'gp2009')
            self.assertEquals(0, len(commits))
        finally:
            datetime.datetime = backup

    def test_backport_in_time(self):
        models.Commit.objects.create(
            revision=147116,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 10, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147117,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 12, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147122,
            path='gp2009/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 2, 12, 24, tzinfo=timezone.utc))
        commits = backport_backend.get_commits('gp2006', 'gp2009')
        self.assertEquals(0, len(commits))

    def test_backport_before_commit(self):
        models.Commit.objects.create(
            revision=147116,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 10, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147117,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 12, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147115,
            path='gp2009/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2015, 12, 31, 12, 24, tzinfo=timezone.utc))
        commits = backport_backend.get_commits('gp2006', 'gp2009')
        self.assertEquals(0, len(commits))

    def test_backport_too_early(self):
        models.Commit.objects.create(
            revision=147116,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 10, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147117,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 12, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147115,
            path='gp2009/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2015, 12, 25, 12, 24, tzinfo=timezone.utc))
        commits = backport_backend.get_commits('gp2006', 'gp2009')
        self.assertEquals(1, len(commits))

    def test_backported_manually_already(self):
        models.Commit.objects.create(
            revision=147116,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 10, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147117,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 12, 24, tzinfo=timezone.utc))
        models.Commit.objects.create(
            revision=147122,
            path='gp2009/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 6, 12, 24, tzinfo=timezone.utc))
        commit = get_object_or_404(models.Commit, revision=147117)
        bp_models.Record.objects.create(
            commit=commit,
            backported=True,
            from_version='gp2006',
            to_version='gp2009')
        commits = backport_backend.get_commits('gp2006', 'gp2009')
        self.assertEquals(0, len(commits))


class TestHidecommit(TransactionTestCase):
    def test_hide_commit_record_exist(self):
        from_version = 'gp2006'
        to_version = 'gp2009'
        revision = 147117
        models.Commit.objects.create(
            revision=147117,
            path='gp2006/adl/src/bib/bibsaisie/bibsaisielisteobjetdvspsfv4.bib',
            username='hhu',
            commit_date=datetime.datetime(2016, 1, 1, 12, 24, tzinfo=timezone.utc))
        commit = get_object_or_404(models.Commit, revision=revision)
        bp_models.Record.objects.create(
            commit=commit,
            backported=False,
            from_version=from_version,
            to_version=to_version)
        backport_backend.hide_commit(commit, from_version, to_version)
        records = bp_models.Record.objects.filter(commit=commit)
        self.assertEqual(1, len(records))
        self.assertEqual(True, records[0].backported)


if __name__ == '__main__':
    unittest.main()
