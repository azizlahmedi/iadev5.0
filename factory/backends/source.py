# -*- coding: utf-8 -*-
import glob
import os
import pprint
import re
import shutil
import tempfile

from delia_tokenizer.ctokenize import ScannerFromFile

import delia_tokenizer
from delia_commons.deliafile import path_name_convert
from delia_preprocessor.deliaobject import DeliaObject
from delia_preprocessor.iterator import fill
from delia_preprocessor.provider import FileProvider
from delia_preprocessor.provider import IProvider
from factory import consts
from factory.backends.base import delia_context, get_project_path, tar


class SubversionProvider(IProvider):
    def __init__(self, subversion_backend, url, work, revision):
        self.subversion_backend = subversion_backend
        self.url = url
        self.work = work
        self.revision = revision

    def get(self, ctx, is_text, text, father=None):
        path = path_name_convert(ctx, text, is_text, father=father)
        if not os.path.exists(path):
            url = path.replace(os.path.dirname(ctx.project_path), self.url, 1)
            self.subversion_backend.export(url, path, self.revision)
        return fill(ScannerFromFile(path, skip_ws=True)), path


class SourceBackend(object):
    def __init__(self, subversion_backend, url):
        self.subversion_backend = subversion_backend
        self.url = url

    def create_tgz(self, schema_version, procedure_name, revision, path):
        with tempfile.TemporaryDirectory() as work:
            project_path = self.export_project(schema_version, work, revision)
            ctx = delia_context()
            ctx.initialize(project_path)
            provider = SubversionProvider(self.subversion_backend, self.url, work, revision)
            files = set()
            object_names = [consts.SCHEMA_NAME, ]
            if procedure_name != consts.SCHEMA_NAME:
                object_names.append(procedure_name)
            for object_name in object_names:
                delia_object = DeliaObject(object_name, provider=provider)
                for _ in delia_object.get_scanner_include():
                    pass
                files.update(delia_object.files)
            minimal_mv(ctx, work)
            tar(path, work)

    def export_project(self, schema_version, work, revision):
        all_rel_path = (
            'mv.py',
            os.path.join('gp%d' % schema_version, 'project.cfg'),
        )
        for rel_path in all_rel_path:
            url = '%s/%s' % (self.url, rel_path.replace(os.path.sep, '/'))
            path = os.path.join(work, rel_path)
            d = os.path.dirname(path)
            if not os.path.exists(d):
                os.makedirs(d)
            self.subversion_backend.export(url, path, revision)
        return get_project_path(work, schema_version)

    def expanse_includes(self, schema_version, procedure_name, bundle_path, expanse_path):
        ctx = delia_context()
        ctx.initialize(os.path.join(bundle_path, 'gp%d' % schema_version))
        os.makedirs(os.path.dirname(expanse_path), exist_ok=True)
        with open(expanse_path, 'w', encoding='latin1') as fd:
            for lexeme in DeliaObject(procedure_name, provider=FileProvider(skip_ws=False)).get_scanner_include():
                fd.write(delia_tokenizer.get_token(*lexeme))
        return expanse_path

    def rename(self, schema_version, procedure_name, procedure_new_name, bundle_path):
        # Check if needed
        if procedure_name == procedure_new_name:
            return
        # Shortcuts
        procedure_basename = procedure_name.replace('.', '_')
        procedure_new_basename = procedure_new_name.replace('.', '_')
        # Java
        java_dir = os.path.join(bundle_path, 'gp%d' % schema_version, 'adl', 'src', 'gra', 'java')
        java_procedure_dir = os.path.join(java_dir, procedure_basename)
        java_procedure_new_dir = os.path.join(java_dir, procedure_new_basename)
        if os.path.isdir(java_procedure_dir):
            shutil.copytree(java_procedure_dir, java_procedure_new_dir)
            java_encoding = 'latin1' if schema_version <= 2009 else 'utf-8'
            for java_new_path in glob.glob(os.path.join(java_procedure_new_dir, 'frm_*.java')):
                with open(java_new_path, 'r', encoding=java_encoding) as java_new_fd:
                    java_new_content = java_new_fd.read()
                java_new_content = java_new_content.replace(procedure_basename, procedure_new_basename)
                with open(java_new_path, 'w', encoding=java_encoding) as java_new_fd:
                    java_new_fd.write(java_new_content)
        # Conf
        conf_dir = os.path.join(bundle_path, 'gp%d' % schema_version, 'adl', 'src', 'conf')
        conf_procedure_path = os.path.join(conf_dir, procedure_basename + '.conf')
        conf_procedure_new_path = os.path.join(conf_dir, procedure_new_basename + '.conf')
        if os.path.isfile(conf_procedure_path):
            shutil.copy(conf_procedure_path, conf_procedure_new_path)
        # Jasper
        jasper_dir = os.path.join(bundle_path, 'gp%d' % schema_version, 'adl', 'src', 'jasper')
        jasper_procedure_dir = os.path.join(jasper_dir, procedure_basename)
        jasper_procedure_new_dir = os.path.join(jasper_dir, procedure_new_basename)
        if os.path.isdir(jasper_procedure_dir):
            shutil.copytree(jasper_procedure_dir, jasper_procedure_new_dir)
        # Procedure path
        for mag_dir in glob.glob(os.path.join(bundle_path, 'gp*', 'adl', 'src', 'mag')):
            procedure_path = os.path.join(mag_dir, procedure_name.replace('.', os.path.sep), procedure_basename + '.adl')
            procedure_new_path = os.path.join(mag_dir, procedure_new_name.replace('.', os.path.sep), procedure_new_basename + '.adl')
            if os.path.isfile(procedure_path):
                os.makedirs(os.path.dirname(procedure_new_path), exist_ok=True)
                shutil.copy(procedure_path, procedure_new_path)
                with open(procedure_new_path, 'r', encoding='latin1') as procedure_new_fd:
                    procedure_new_content = procedure_new_fd.read()
                # Handle "PROCEDURE X.Y.Z"
                procedure_new_content = re.sub(re.escape(procedure_name), procedure_new_name, procedure_new_content, count=1, flags=re.IGNORECASE)
                # Handle "chainage"
                procedure_new_content = re.sub(re.escape(procedure_name.replace('.', '_') + '.ADL'), procedure_new_name.replace('.', '_') + '.ADL', procedure_new_content, count=1, flags=re.IGNORECASE)
                with open(procedure_new_path, 'w', encoding='latin1') as procedure_new_fd:
                    procedure_new_fd.write(procedure_new_content)
        # I18n
        mlg_dir = os.path.join(bundle_path, 'gp%d' % schema_version, 'adl', 'src', 'mlg')
        if os.path.isdir(mlg_dir):
            for lang in os.listdir(mlg_dir):
                po_path = os.path.join(mlg_dir, lang, '%s_%s.po' % (procedure_basename, lang))
                po_new_path = os.path.join(mlg_dir, lang, '%s_%s.po' % (procedure_new_basename, lang))
                if os.path.isfile(po_path):
                    shutil.copy(po_path, po_new_path)

    def get_head_revision(self):
        return self.subversion_backend.get_head_revision(self.url)


project_name_re = re.compile('^gp(\d+)$')


def minimal_mv(ctx, work):
    all_procedure_names = {}
    for project_name in os.listdir(work):
        m = project_name_re.match(project_name)
        if m:
            schema_version = int(m.group(1))
            all_procedure_names[schema_version] = set()
            for root, dirs, files in os.walk(os.path.join(work, project_name, 'adl', 'src', 'mag')):
                if '.svn' in dirs:
                    dirs.remove('.svn')
                for basename in files:
                    if basename.endswith('.adl'):
                        all_procedure_names[schema_version].add(basename[:-len('.adl')].lower().replace('_', '.'))
    new_mv = {}
    new_r_mv = {}
    for schema_version, procedure_names in all_procedure_names.items():
        if schema_version in ctx.mv:
            for procedure_name in procedure_names:
                if procedure_name in ctx.mv[schema_version]:
                    if schema_version not in new_mv:
                        new_mv[schema_version] = {}
                    data = ctx.mv[schema_version][procedure_name]
                    new_mv[schema_version][procedure_name] = data
                    procedure_hash = data.get('hash')
                    if procedure_hash:
                        if schema_version not in new_r_mv:
                            new_r_mv[schema_version] = {}
                        new_r_mv[schema_version][procedure_hash] = procedure_name
    content = '''#-*- coding: utf-8 -*-
mv = %s
r_mv = %s
''' % (pprint.pformat(new_mv), pprint.pformat(new_r_mv))
    compile(content, 'mv.py', 'exec')  # checks if compiles
    with open(os.path.join(work, 'mv.py'), 'w', encoding='utf-8') as fd:
        fd.write(content)
