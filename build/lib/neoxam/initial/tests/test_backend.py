import neoxam.tests

neoxam.tests.setup()

from django.test import TransactionTestCase
import datetime
from neoxam.initial import consts
from neoxam.initial import backends as initial_backends
from neoxam.versioning import models
from neoxam.initial import models as initial_models
from django.utils import timezone


class MyDatetime(datetime.datetime):
    @classmethod
    def now(cls):
        return datetime.datetime(2016, 1, 2, 12, 24, tzinfo=timezone.utc)

    @classmethod
    def utcnow(cls):
        return datetime.datetime(2016, 1, 2, 12, 24, tzinfo=timezone.utc)


def my_now():
    return datetime.datetime(2016, 1, 2, 12, 24, tzinfo=timezone.utc)


class TestGetInitialCommits(TransactionTestCase):
    def setUp(self):
        TransactionTestCase.setUp(self)
        self.datetime_backup = datetime.datetime
        self.timezone_now_backup = timezone.now
        self.starting_revision_backup = consts.STARTING_REVISION
        consts.STARTING_REVISION = 5
        datetime.datetime = MyDatetime
        timezone.now = my_now

    def tearDown(self):
        datetime.datetime = self.datetime_backup
        timezone.now = self.timezone_now_backup
        consts.STARTING_REVISION = self.starting_revision_backup
        models.AdlObj.objects.all().delete()
        initial_models.InitialCommitRecord.objects.all().delete()
        TransactionTestCase.tearDown(self)

    def test_too_early_to_check(self):
        models.AdlObj.objects.create(
            version=2009,
            local="bib",
            name="bibtest",
            ext="bib",
            vmsdate=datetime.datetime(2016, 1, 1, 16, 0, tzinfo=timezone.utc),
            svndate=datetime.datetime(2016, 1, 1, 16, 0, tzinfo=timezone.utc),
            checksum="somestring",
            user="tester",
            revision=4,
            sent=12,
            frame=13,
        )
        commits = initial_backends.initialcommitbackend.get_initial_commits(2009)
        self.assertEquals(0, len(commits))

    def test_initial_commit(self):
        models.AdlObj.objects.create(
            version=2009,
            local="bib",
            name="bibtest1",
            ext="bib",
            vmsdate=datetime.datetime(2015, 1, 1, 16, 0, tzinfo=timezone.utc),
            svndate=datetime.datetime(2015, 1, 1, 16, 0, tzinfo=timezone.utc),
            checksum="somestring",
            user="tester",
            revision=10,
            sent=12,
            frame=13,
        )
        commits = initial_backends.initialcommitbackend.get_initial_commits(2009)
        self.assertEquals(1, len(commits))

    def test_not_initial_commit(self):
        models.AdlObj.objects.create(
            version=2009,
            local="bib",
            name="bibtest1",
            ext="bib",
            vmsdate=datetime.datetime(2015, 1, 1, 16, 0, tzinfo=timezone.utc),
            svndate=datetime.datetime(2015, 1, 1, 16, 0, tzinfo=timezone.utc),
            checksum="somestring",
            user="tester",
            revision=10,
            sent=12,
            frame=13,
        )
        models.AdlObj.objects.create(
            version=2009,
            local="bib",
            name="bibtest1",
            ext="bib",
            vmsdate=datetime.datetime(2014, 1, 1, 16, 0, tzinfo=timezone.utc),
            svndate=datetime.datetime(2014, 1, 1, 16, 0, tzinfo=timezone.utc),
            checksum="somestring",
            user="tester",
            revision=9,
            sent=12,
            frame=13,
        )
        commits = initial_backends.initialcommitbackend.get_initial_commits(2009)
        self.assertEquals(1, len(commits))
        self.assertEquals(datetime.datetime(2014, 1, 1, 16, 0, tzinfo=datetime.timezone.utc), commits[0].svndate)
