# -*- coding: utf-8 -*-


class Eclipse(object):
    @property
    def INSTALLED_APPS(self):
        return super(Eclipse, self).INSTALLED_APPS + ['neoxam.eclipse', ]
