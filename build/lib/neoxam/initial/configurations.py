# -*- coding: utf-8 -*-


class InitialCommit(object):
    @property
    def INSTALLED_APPS(self):
        return super(InitialCommit, self).INSTALLED_APPS + ['neoxam.initial', ]
