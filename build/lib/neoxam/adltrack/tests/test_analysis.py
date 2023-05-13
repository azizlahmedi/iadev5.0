# -*- coding: utf-8 -*-
import neoxam.tests

neoxam.tests.setup()

import os
import unittest
from django.utils import timezone
from django.test import TransactionTestCase

from neoxam.adltrack import models
from neoxam.adltrack.backends import AnalysisBackend
from neoxam.scm.tests.base import MockRepositoryBackend
from neoxam.versioning.models import AdlObj

BASE = os.path.dirname(os.path.abspath(__file__))


class AnalysisTestCase(TransactionTestCase):
    def setUp(self):
        super(AnalysisTestCase, self).setUp()
        self.root = os.path.join(BASE, 'adl')
        self.repository_backend = MockRepositoryBackend(self.root)
        self.analysis_backend = AnalysisBackend(self.repository_backend)
        self.ctx = self.analysis_backend.get_context(self.root, 2009)

    def test_process_procedure(self):
        data = self.analysis_backend.process_procedure(self.root, 'test')
        expected_data = {'macros': [{'count_calls': 1,
                                     'name': 'my.macro',
                                     'path': 'gp2009/adl/src/bib/others/bibtest.bib'},
                                    {'count_calls': 0,
                                     'name': 'my.macro2',
                                     'path': 'gp2009/adl/src/mag/test/test.adl'}],
                         'paths': ['gp2009/adl/src/mag/test/test.adl', 'gp2009/adl/src/bib/others/bibtest.bib'],
                         'count_tokens': 8}
        self.assertEqual(expected_data, data)

    def test_must_process_procedure(self):
        self.assertTrue(self.analysis_backend.must_process_procedure(False, self.ctx, None, 2009, 'test'))
        self.assertFalse(self.analysis_backend.must_process_procedure(False, self.ctx, None, 2009, 'not.exist'))

    def test_get_procedure_names(self):
        procedure_names = self.analysis_backend.get_procedure_names(self.ctx)
        self.assertEqual(['test'], list(procedure_names))

    def test_process(self):
        AdlObj.objects.create(
            version=2009,
            local='mag',
            name='test',
            ext='adl',
            revision=138000,
            svndate=timezone.now(),
            user='omansion',
        )
        self.analysis_backend.process()
        commit = models.Commit.objects.get()
        self.assertEqual(138000, commit.revision)
        procedure = models.Procedure.objects.get()
        self.assertEqual('test', procedure.name)
        procedure_version = models.ProcedureVersion.objects.get()
        self.assertEqual(8, procedure_version.data['count_tokens'])


if __name__ == '__main__':
    unittest.main()
