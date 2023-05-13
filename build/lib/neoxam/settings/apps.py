# -*- coding: utf-8 -*-
import os

from neoxam.settings.base import Mixin



class UI(Mixin):
    @property
    def INSTALLED_APPS(self):
        return super(UI, self).INSTALLED_APPS + [
            'neoxam.jquery',
            'neoxam.bootstrap',
            'neoxam.fontawesome',
        ]


class Commons(Mixin):
    @property
    def INSTALLED_APPS(self):
        return super(Commons, self).INSTALLED_APPS + ['neoxam.commons', ]


class Elastic(Mixin):
    @property
    def INSTALLED_APPS(self):
        return super(Elastic, self).INSTALLED_APPS + ['neoxam.elastic', ]


class ADLTrack(Mixin):
    pass


class Versioning(Mixin):
    pass




class Factory(Mixin):

        
    @property
    def FACTORY_SETTINGS(self):
        return os.path.join(self.ROOT, 'etc', 'factory_%(schema_version)s.cfg')

    @property
    def FACTORY_SUPPORT_HOMES(self):
        return os.path.join(self.ROOT, 'var', 'lib', 'factory')




class Eclipse(Mixin):
    @property
    def ECLIPSE_TMP(self):
        return os.path.join(self.ROOT, 'tmp', 'eclipse')

    @property
    def ECLIPSE_PUBLISH_ROOT(self):
        return os.path.join(self.ROOT, 'var', 'www', 'eclipse')

    @property
    def ECLIPSE_DELIVER_TEST_ROOT(self):
        return os.path.join(self.ROOT, 'var', 'www', 'gp', '{schema_version}-dev')


class SCM(Mixin):
    @property
    def INSTALLED_APPS(self):
        return super(SCM, self).INSTALLED_APPS + ['neoxam.scm', ]

    @property
    def SCM_CHECKOUT_DIR(self):
        return os.path.join(self.ROOT, 'var', 'scm')


class Locks(Mixin):
    @property
    def INSTALLED_APPS(self):
        return super(Locks, self).INSTALLED_APPS + ['neoxam.dblocks', ]

    DBLOCKS_DATABASE_ALIAS = 'locks'





class Backport(Mixin):
    @property
    def BACKPORT_CACHE_DIR(self):
        return os.path.join(self.ROOT, 'var', 'backport')


class Webintake(Mixin):
    @property
    def WEBINTAKE_ROOT(self):
        return os.path.join(self.ROOT, 'var', 'webintake')
