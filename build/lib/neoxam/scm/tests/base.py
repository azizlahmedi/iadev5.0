# -*- coding: utf-8 -*-
import contextlib


class MockSubversionBackend(object):
    def __init__(self, root):
        self.root = root

    def checkout(self, revision=None):
        pass


class MockRepositoryBackend(object):
    def __init__(self, root):
        self.root = root

    @contextlib.contextmanager
    def checkout_context(self, key):
        yield MockSubversionBackend(self.root)
