# -*- coding: utf-8 -*-

class Backport(object):
    @property
    def INSTALLED_APPS(self):
        return super(Backport, self).INSTALLED_APPS + ['neoxam.backport', ]
