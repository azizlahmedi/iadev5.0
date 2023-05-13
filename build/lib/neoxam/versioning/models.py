# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import io
import os

import pytz
import sys
import time
from django.db import models
from neoxam.versioning import managers


class AdlCadre(models.Model):
        
    version = models.IntegerField(blank=True, null=True)
    adlobj_id = models.IntegerField(blank=True, null=True)
    uptodate = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'adl_cadre'
        app_label = 'versioning'


class AdlObj(models.Model):
    
    FOLDERS = {'mag': 'mag',
               'bib': 'bib',
               'ent': 'msg/entete',
               'msg': 'msg/divers',
               'hlp': 'msg/help',
               'frm': 'msg/frame',
               'agl': 'agl',
               'amg': 'agl/msg',
               'rc': 'gra/rc',
               'rc1': 'gra/tmp',
               'magui': 'magui',
               'mlg': 'mlg',
               'java': 'gra/java/monolang/java',
               'crf': 'crf',
               'lib': 'DISK$300P:[SYS0.SYSCOMMON.MAGNUM.LIBRARY]', }

    LIBRARY_PREFIXES = ('bibsaisie',
                        'bibverif',
                        'bibconvert',
                        'bibcalcul',
                        'bibaffiche',
                        'bibcherche',
                        'bibparam',
                        'bibconsult',
                        'bibcontrol',
                        'bibvalo',
                        'bibtraite',)
    LIBRARY_DEFAULT_PREFIX = 'others'

    version = models.IntegerField()
    local = models.CharField(max_length=16)
    name = models.CharField(max_length=256)
    ext = models.CharField(max_length=16)
    vmsdate = models.DateTimeField(blank=True, null=True)
    svndate = models.DateTimeField(blank=True, null=True)
    checksum = models.CharField(max_length=256, blank=True, null=True)
    user = models.CharField(max_length=256, blank=True, null=True)
    revision = models.IntegerField(blank=True, null=True)
    sent = models.IntegerField(blank=True, null=True)
    frame = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'adl_obj'
        app_label = 'versioning'

    @property
    def dirname(self):
        return self.FOLDERS[self.local]

    def venus_path(self):
        checkout = '/workspace/src/gp'
        if checkout not in sys.path:
            sys.path.append(checkout)
        from mv import mv
        basename = self.name + '.' + self.ext
        if self.local == 'mag':
            if self.name not in mv[self.version]:
                return
            basename = mv[self.version][self.name]['hash'] + '.me0'
        return self.dirname + '/' + basename

    def get_date(self, cx):
        buffer = io.StringIO()

        def write(line):
            buffer.writelines('%s\n' % line)

        venus_path = self.venus_path()
        if not venus_path:
            return
        cx.dir(self.venus_path(), write)
        buffer.seek(0)
        content = buffer.read()
        buffer.close()
        data = parse_folder(content)
        if len(data) == 0:
            return
        return data[0][1]

    def get_venus_content(self, cx):
        buffer = io.StringIO()

        def to_buffer(line):
            buffer.writelines('%s\n' % line)

        cx.retrlines('RETR %s' % self.venus_path(), to_buffer)
        buffer.seek(0)
        content = buffer.read()
        buffer.close()
        return content

    def get_svn_path(self):
        args = ['gp%d' % self.version, 'adl', 'src']
        args.extend(self.dirname.split('/'))
        if self.local == 'mag':
            args.extend(self.name.split('.'))
            args.append(self.name.replace('.', '_') + '.' + self.ext)
        else:
            if self.local == 'bib':
                args.append(self._library_prefix(self.name))
            args.append(self.name + '.' + self.ext)
        return os.path.join(*args)

    def _library_prefix(self, name):
        for prefix in self.LIBRARY_PREFIXES:
            if name.startswith(prefix):
                return prefix
        return self.LIBRARY_DEFAULT_PREFIX

    def __str__(self):
        return self.get_svn_path()

    @property
    def command_line_key(self):
        if self.local == 'mag':
            return self.name
        return '%s:%s.%s' % (self.local, self.name, self.ext)


def parse_folder(sdir):
    '''
    Parse the result of a dir on VMS
    '''
    res = []
    lines = [line.strip() for line in sdir.split('\n')]
    index = 0
    while index < len(lines):
        line = lines[index]
        if line == line.upper() and line != '':
            while len(line.split()) < 5:
                index += 1
                line += " %s" % lines[index]
            data = line.split()
            assert len(data) == 6
            toparse = " ".join(data[2:4])
            mytime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(toparse, "%d-%b-%Y %H:%M:%S")),
                                                     tz=pytz.utc)
            res.append((data[0], mytime))
        index += 1
    return res


class CommentType(models.Model):
        
    iso = models.CharField(max_length=256)
    description = models.CharField(max_length=1024)
    deftype = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'comment_type'
        app_label = 'versioning'


class Comment(models.Model):
    
    technical_comment = models.CharField(max_length=1024)
    functional_comment = models.CharField(max_length=1024, blank=True, null=True)
    reference = models.CharField(max_length=1024, blank=True, null=True)
    type_object = models.CharField(max_length=256, blank=True, null=True)
    external_id = models.CharField(max_length=256, blank=True, null=True)
    user = models.CharField(max_length=256)
    adlobj = models.OneToOneField(AdlObj, on_delete=models.CASCADE,db_column='adlobj_id', related_name='comment')
    is_user_doc = models.CharField(max_length=1, blank=True, null=True)
    date_time = models.DateTimeField(blank=True, null=True)
    comment_type = models.ForeignKey(CommentType, on_delete=models.CASCADE,db_column='ctype_id')

    class Meta:
        db_table = 'comment'
        app_label = 'versioning'


class Compilation(models.Model):
    cdate = models.DateTimeField(blank=True, null=True)
    maxrev = models.IntegerField(blank=True, null=True)
    adlobj = models.ForeignKey(AdlObj, on_delete=models.CASCADE,db_column='adlobj_id', blank=True, null=True)
    r_maxrev = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'compilation'
        app_label = 'versioning'

    objects = managers.CompilationManager()


class Dependences(models.Model):
    adl_cadre_id = models.IntegerField()
    adl_obj_id = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'dependences'
        app_label = 'versioning'

class Language(models.Model):
    iso = models.CharField(max_length=32)
    description = models.CharField(max_length=1024)

    class Meta:
        db_table = 'language'
        app_label = 'versioning'


class Oversee(models.Model):
    date = models.DateTimeField(blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'oversee'
        app_label = 'versioning'


class Statistic(models.Model):
    version = models.IntegerField()
    opt = models.CharField(max_length=256)
    fast = models.IntegerField()
    bin = models.IntegerField()
    listing = models.IntegerField()
    start = models.DateTimeField()
    stop = models.DateTimeField()
    alpha = models.FloatField(blank=True, null=True)
    # Was the MP0 compiled
    compiled = models.IntegerField()
    # Was the process successful
    error = models.IntegerField()
    cause = models.CharField(max_length=4096, blank=True, null=True)
    i18n = models.FloatField(blank=True, null=True)
    cuts = models.FloatField(blank=True, null=True)
    gui = models.FloatField(blank=True, null=True)
    klass = models.FloatField(blank=True, null=True)
    ftp_count = models.IntegerField(blank=True, null=True)
    # Included in tree elapsed
    ftp_elapsed = models.FloatField(blank=True, null=True)
    ftp_size = models.FloatField(blank=True, null=True)
    delia_count = models.IntegerField(blank=True, null=True)
    # Included in tree elapsed
    delia_elapsed = models.FloatField(blank=True, null=True)
    delia_size = models.FloatField(blank=True, null=True)
    tree_count = models.IntegerField(blank=True, null=True)
    tree_elapsed = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'statistic'
        app_label = 'versioning'

    def as_es_doc(self):
        elapsed = (self.stop - self.start).total_seconds()
        timestamp = int(time.mktime(self.start.timetuple()) * 1000)
        data = {
            '@timestamp': timestamp,
            'external_id': self.pk,
            'procedure': {
                'version': '%s' % self.version,
                'name': self.opt,
            },
            'params': {
                'normal': int(not self.fast),
                'no_save': int(not self.bin),
                'list_to_file': self.listing,
            },
            'success': {
                'all': int(not self.error),
                'magnum': self.compiled,
            },
            'elapsed': {
                'dependencies': if_none_0(self.tree_elapsed),
                'magnum': if_none_0(self.alpha),
                'mlg': if_none_0(self.i18n),
                'magui': if_none_0(self.gui),
                'classes': if_none_0(self.klass),
            }
        }
        data['elapsed']['other'] = max(0, elapsed - sum(data['elapsed'].values()))
        data['elapsed']['all'] = float(elapsed)
        for index, name in list(enumerate(self.opt.split('.'), start=1))[:9]:
            data['procedure']['name%d' % index] = name
        return data


def if_none_0(value):
    if not value:
        return 0
    return value


class Translation(models.Model):
    content = models.CharField(max_length=1024)
    status = models.CharField(max_length=1)
    date_time = models.DateTimeField(blank=True, null=True)
    comment_id = models.IntegerField(blank=True, null=True)
    language_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'translation'
        app_label = 'versioning'


class User(models.Model):
    login = models.CharField(max_length=256)
    role = models.CharField(max_length=256)

    class Meta:
        db_table = 'user'
        app_label = 'versioning'
