# -*- coding: utf-8 -*-
import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def fisheye_revision_url(commit):
    return mark_safe('https://access.my-nx.com/fisheye/changelog/GP3_ADL?cs=%s' % commit.revision)


@register.filter
def viewvc_revision_url(commit):
    return mark_safe(
        'https://access.my-nx.com/svn/viewvc/gp/trunk/%s?view=log&pathrev=%s' % (commit.path, commit.revision))


@register.filter
def addstr(arg1, arg2):
    return ''.join(map(str, (arg1, arg2,)))


@register.filter
def replace(string, args):
    "`args` is in the following format: [delim_char]regex search[delim_char]regex replace"
    __, search, replace, = args.split(args[0])
    return re.sub(search, replace, string)
