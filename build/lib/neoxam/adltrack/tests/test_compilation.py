# -*- coding: utf-8 -*-
import neoxam.tests

neoxam.tests.setup()

import unittest
from django.utils import timezone
from django.test import TransactionTestCase

from neoxam.adltrack import models, backends, consts
from neoxam.versioning.models import AdlObj, Compilation
from neoxam.dblocks.models import Lock


class CompilationTestCase(TransactionTestCase):
    def setUp(self):
        super(CompilationTestCase, self).setUp()
        Lock.objects.all().delete()

    def create_procedure_version(self, version, procedure_name, revision):
        procedure = models.Procedure.objects.create(version=version, name=procedure_name)
        commit = models.Commit.objects.create(revision=revision, path='toto.txt', commit_date=timezone.now())
        return models.ProcedureVersion.objects.create(procedure=procedure, commit=commit)

    def create_compilation(self, version, procedure_name, revision):
        adlobj = AdlObj.objects.create(
            version=version,
            local='mag',
            name=procedure_name,
            ext='adl',
            revision=revision - 1000,
        )
        return Compilation.objects.create(
            maxrev=revision,
            adlobj=adlobj,
        )

    def test(self):
        revision = 200000
        version = 2009
        procedure_name = 'test'
        compilation = self.create_compilation(version, procedure_name, revision)
        procedure_version = self.create_procedure_version(version, procedure_name, revision)
        self.assertFalse(procedure_version.magnum_compiled)
        backends.compilation_backend.collect()
        procedure_version.refresh_from_db()
        self.assertTrue(procedure_version.magnum_compiled)
        etl = Lock.objects.get(name=consts.COMPILATION_LOCK)
        self.assertEqual(compilation.pk, etl.data['foreign_id'])


if __name__ == '__main__':
    unittest.main()
