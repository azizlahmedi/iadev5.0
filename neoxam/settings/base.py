# -*- coding: utf-8 -*-
from django.core import signing



class Mixin(object):
    def decrypt(self, encrypted):
        return signing.loads(encrypted, key=self.SECRET_KEY)
