# -*- coding: utf-8 -*-


class Delivery(object):
    @property
    def INSTALLED_APPS(self):
        return super(Delivery, self).INSTALLED_APPS + ['neoxam.delivery', ]
