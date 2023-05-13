# -*- coding: utf-8 -*-
import neoxam.tests

neoxam.tests.setup()

import unittest
from django.test import TransactionTestCase

from neoxam.scm import models, backends


class CheckoutTestCase(TransactionTestCase):
    def setUp(self):
        super(CheckoutTestCase, self).setUp()
        self.repository = models.Repository.objects.create(
            key='toto',
            url='https://access.my-nx.com/svn/repos/ntic_test/trunk/test_oma/dateoverride',
            timeout=60,
        )

    def test_checkout(self):
        with backends.repository_backend.checkout_context(self.repository.key) as scm_backend:
            scm_backend.checkout()
            data, output = scm_backend.info()
            self.assertEqual(self.repository.url, data['URL'])
            root = scm_backend.root
        with backends.repository_backend.checkout_context(self.repository.key) as scm_backend:
            scm_backend.checkout()
            self.assertEqual(root, scm_backend.root)

    def test_lock(self):
        with backends.repository_backend.checkout_context(self.repository.key) as scm_backend1:
            with backends.repository_backend.checkout_context(self.repository.key) as scm_backend2:
                self.assertNotEqual(scm_backend1.root, scm_backend2.root)

    def test_url_change(self):
        with backends.repository_backend.checkout_context(self.repository.key) as scm_backend:
            scm_backend.checkout()
        self.repository.url = 'http://avalon.bams.corp:3180/svn/repos/ntic_test/trunk/test_oma/gpdiff'
        self.repository.save(update_fields=('url',))
        with backends.repository_backend.checkout_context(self.repository.key) as scm_backend:
            scm_backend.checkout()
            data, output = scm_backend.info()
            self.assertEqual(self.repository.url, data['URL'])


if __name__ == '__main__':
    unittest.main()
