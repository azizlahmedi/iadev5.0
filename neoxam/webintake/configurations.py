# -*- coding: utf-8 -*-

class Webintake(object):
    @property
    def INSTALLED_APPS(self):
        return super(Webintake, self).INSTALLED_APPS + ['neoxam.webintake', ]
