# -*- coding: utf-8 -*-

class Gpatcher(object):
    @property
    def INSTALLED_APPS(self):
        return super(Gpatcher, self).INSTALLED_APPS + ['neoxam.gpatcher',]
