# -*- coding: utf-8 -*-

class Harry(object):
    @property
    def INSTALLED_APPS(self):
        return super(Harry, self).INSTALLED_APPS + ['neoxam.harry', ]

