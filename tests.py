# -*- coding: utf-8 -*-

def setup():
    import os

    os.environ['DJANGO_SETTINGS_MODULE'] = 'neoxam.settings'
    os.environ['DJANGO_CONFIGURATION'] = 'Test'
    from configurations import importer

    importer.install()

    import django
    django.setup()
