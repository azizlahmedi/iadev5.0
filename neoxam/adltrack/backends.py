# -*- coding: utf-8 -*-
import enum
import logging
import os

import pytz
import xlsxwriter
from django.conf import settings
from django.db import transaction
from django.db.models import Max, Min
from django.shortcuts import get_object_or_404
from django.utils import timezone

import delia_commons
from delia_commons.singleton import Singleton
from delia_preprocessor import events
from delia_preprocessor.include import scan_include
from delia_preprocessor.macro import scan_macro
from factory.deliaobject import Procedure
from neoxam.adltrack import models, consts
from neoxam.dblocks.backends import lock_backend
from neoxam.scm.backends import repository_backend
from neoxam.versioning.models import AdlObj, Compilation

log = logging.getLogger(__name__)

# 2009/ihm.menu3@131035
TEST = False


class AnalysisBackend(object):
    def __init__(self, repository_backend):
        self.repository_backend = repository_backend

    def get_current_revision(self):
        try:
            return models.Commit.objects.latest().revision
        except models.Commit.DoesNotExist:
            if TEST:
                return 131035 - 1
            return AdlObj.objects.aggregate(Max('revision'))['revision__max'] - 1

    def get_procedure_names(self, ctx):
        mag_dir = ctx.logical_names['magnum_default_directory']
        if os.path.isdir(mag_dir):
            for root, dirs, files in os.walk(mag_dir):
                for f in files:
                    if f.endswith('.adl'):
                        procedure_name = f[:-4].replace('_', '.')
                        yield procedure_name

    def process(self, full=False):
        current_revision = self.get_current_revision()
        adl_objects = AdlObj.objects.filter(revision__gt=current_revision).order_by('revision')
        for adl_object in adl_objects:
            with self.repository_backend.checkout_context(consts.REPOSITORY_KEY) as scm_backend:
                with transaction.atomic():
                    scm_backend.checkout(adl_object.revision)
                    path = adl_object.get_svn_path()
                    commit = models.Commit.objects.create(
                        revision=adl_object.revision,
                        username=adl_object.user,
                        commit_date=timezone.utc.normalize(
                            pytz.timezone('Europe/Paris').localize(adl_object.svndate.replace(tzinfo=None)).astimezone(
                                timezone.utc)),
                        path=path,
                    )
                    count_procedures = 0
                    count_tokens = 0
                    count_procedures_analyzed = 0
                    delta_tokens = 0
                    for version in consts.ANALYZE_VERSIONS:
                        ctx = self.get_context(scm_backend.root, version)
                        if ctx:
                            try:
                                procedure_names = self.get_procedure_names(ctx)
                                for procedure_name in procedure_names:
                                    if self.must_process_procedure(full, ctx, commit, version, procedure_name):
                                        log.info('process %d/%s@%d', version, procedure_name, commit.revision)
                                        analyzed = True
                                        try:
                                            data = self.process_procedure(scm_backend.root, procedure_name)
                                        except:
                                            log.exception('failed to process %d/%s@%d', version, procedure_name,
                                                          commit.revision)
                                            data = {}
                                            analyzed = False
                                        if full or not analyzed or path in data['paths']:
                                            procedure = models.Procedure.objects.get_or_create(
                                                version=version,
                                                name=procedure_name,
                                            )[0]
                                            if analyzed:
                                                analyzed_procedure_version = procedure.latest_version(analyzed=True)
                                                data.update({
                                                    'delta_tokens': 0 if not analyzed_procedure_version else
                                                    (data['count_tokens'] - analyzed_procedure_version.data[
                                                        'count_tokens'])
                                                })
                                                count_tokens += data['count_tokens']
                                                count_procedures_analyzed += 1
                                                delta_tokens += data['delta_tokens']
                                            count_procedures += 1
                                            models.ProcedureVersion.objects.filter(procedure=procedure).update(
                                                head=False)
                                            models.ProcedureVersion.objects.create(
                                                procedure=procedure,
                                                commit=commit,
                                                data=data,
                                                head=True,
                                                analyzed=analyzed,
                                            )
                            finally:
                                Singleton.reset(ctx)
                    commit.data = {
                        'count_procedures': count_procedures,
                        'count_procedures_analyzed': count_procedures_analyzed,
                        'count_tokens': count_tokens,
                        'delta_tokens': delta_tokens,
                    }
                    commit.save(update_fields=('data',))
                full = False
            if TEST:
                return

    def must_process_procedure(self, full, ctx, commit, version, procedure_name):
        if TEST:
            return version == 2009 and procedure_name == 'ihm.menu3'
        if procedure_name.startswith('bib'):
            return False
        is_svn = ctx.mv[version].get(procedure_name, {}).get('svn', False)
        if not is_svn:
            return False
        if full:
            return True
        try:
            procedure_version = models.ProcedureVersion.objects.filter(
                procedure__version=version,
                procedure__name=procedure_name,
                head=True
            ).get()
        except models.ProcedureVersion.DoesNotExist:
            return True
        if not procedure_version.analyzed:
            return True
        if commit.path in procedure_version.data['paths']:
            return True
        return False

    def get_context(self, root, version):
        project_path = os.path.join(root, 'gp%d' % version)
        if os.path.isdir(project_path):
            ctx = delia_commons.Context()
            ctx.initialize(project_path)
            return ctx

    def process_procedure(self, root, procedure_name):
        procedure = Procedure(procedure_name)
        scanner = procedure.get_scanner()
        tokens = 0
        macro_usage = {}
        for event in scan_macro(
                scan_include(scanner=scanner, path=scanner.path, files=procedure.files, stack=[]),
                acros=procedure.macros, stack=[]):
            event_type = event[0]
            if event_type == events.TOKEN:
                tokens += 1
            elif event_type == events.M_SUB_IN:
                macro = event[1]
                macro_usage[macro.name] = macro_usage.get(macro.name, 0) + 1
        paths = [f[len(root) + 1:] for f in procedure.files]
        macros = []
        for macro in procedure.macros.values():
            macros.append({
                'name': macro.name,
                'path': paths[macro.path_idx],
                'count_calls': macro_usage.get(macro.name, 0),
            })
        macros.sort(key=lambda x: x['count_calls'], reverse=True)
        scanner.destroy()
        return {
            'count_tokens': tokens,
            'paths': paths,
            'macros': macros,
        }


analysis_backend = AnalysisBackend(repository_backend)


class CompilationBackend(object):
    def collect(self, full=False):
        return list(self.collect_iter(full=full))

    def collect_iter(self, full=False):
        foreign_id_key = 'foreign_id'
        with lock_backend.lock(consts.COMPILATION_LOCK) as data:
            revisions = models.Commit.objects.aggregate(Min('revision'), Max('revision'))
            revision_min = revisions.get('revision__min')
            if revision_min is None:
                revision_min = 0
            revision_max = revisions.get('revision__max')
            if revision_max is None:
                revision_max = 0
            log.info('collect compilations')
            foreign_id = data.get(foreign_id_key)
            if foreign_id is None or full:
                foreign_id = 0
            log.info('collect legacy compilations from revision %s to %s with foreign ID > %s', revision_min,
                     revision_max,
                     foreign_id)
            qs = Compilation.objects.filter(
                maxrev__isnull=False,
                maxrev__gte=revision_min,
                maxrev__lte=revision_max,
                pk__gt=foreign_id,
            ).select_related('adlobj').order_by('pk')
            if TEST:
                qs = qs.filter(adlobj__version=2009, adlobj__name='ihm.menu3')
            for compilation in qs:
                procedure_version = None
                # atomic cause if we send a celery task post yield we want the database up to date
                with transaction.atomic():
                    version = compilation.adlobj.version
                    name = compilation.adlobj.name
                    revision = compilation.maxrev
                    try:
                        procedure_version = models.ProcedureVersion.objects.get(
                            procedure__name=name,
                            procedure__version=version,
                            commit__revision=revision,
                        )
                    except models.ProcedureVersion.DoesNotExist:
                        log.error('%d/%s@%d does not exist for compilation %d', version, name, revision, compilation.pk)
                    else:
                        procedure_version.magnum_compiled = True
                        procedure_version.save(update_fields=('magnum_compiled',))
                if procedure_version:
                    yield procedure_version
                foreign_id = compilation.pk
            data.set(foreign_id_key, foreign_id)


compilation_backend = CompilationBackend()


class XLSXBackend:
    @enum.unique
    class Type(enum.IntEnum):
        COMMIT = 1
        MACRO = 2

    class Regex:
        COMMIT = r'^commit_(?P<revision>\d+).xlsx$'
        MACRO = r'^macro_(?P<procname>[^_]+(_[^_]+)*)_(?P<version>\d+)_(?P<revision>\d+).xlsx$'

        @staticmethod
        def commit_filename(revision):
            return "commit_%d.xlsx" % revision

        @staticmethod
        def macro_filename(procname, version, revision):
            return "macro_%s_%d_%d.xlsx" % (procname, version, revision,)

    def process_commit(self, revision):
        if not os.path.isdir(settings.SENDFILE_ROOT):
            os.makedirs(settings.SENDFILE_ROOT)
        path = os.path.join(settings.SENDFILE_ROOT, self.Regex.commit_filename(revision))
        if not os.path.isfile(path):
            commit = get_object_or_404(models.Commit, revision=revision)
            procedure_versions = commit.procedure_versions.select_related('procedure').order_by(
                '-procedure__version',
                'procedure__name',
            )
            with xlsxwriter.Workbook(path) as workbook:
                worksheet = workbook.add_worksheet()
                procedure_headers = ("version", "name",)
                data_headers = ("count_tokens", "delta_tokens", "macros")
                headers = procedure_headers + data_headers
                format_ = workbook.add_format({'bold': True})
                mapping_headers = dict((h, h,) for h in headers)
                mapping_headers.update({
                    "version": "Version",
                    "name": "Name",
                    "count_tokens": "Tokens",
                    "delta_tokens": "\u0394 Tokens",
                    "macros": "Macros"
                })
                mapping_data = dict((h, str,) for h in headers)
                mapping_data.update({
                    "macros": lambda x: str(len(x)),
                })
                for col, header, in enumerate(headers):
                    worksheet.write(0, col, mapping_headers[header], format_)
                for row, procedure_version, in enumerate(procedure_versions):
                    col = 0
                    if procedure_version.analyzed and procedure_version.magnum_compiled:
                        format_ = workbook.add_format({'bg_color': '#5cb85c'})
                    elif procedure_version.analyzed:
                        format_ = workbook.add_format({'bg_color': '#fcf8e3'})
                    else:
                        format_ = workbook.add_format({'bg_color': '#f2dede'})
                    procedure = get_object_or_404(models.Procedure, pk=procedure_version.procedure_id)
                    for header in procedure_headers:
                        worksheet.write(row + 1, col, str(getattr(procedure, header)), format_)
                        col += 1
                    for header in data_headers:
                        try:
                            data = procedure_version.data[header]
                        except KeyError:
                            worksheet.write(row + 1, col, '', format_)
                            col += 1
                        else:
                            worksheet.write(row + 1, col, mapping_data[header](data), format_)
                            col += 1

    def process_macro(self, procname, version, revision):
        if not os.path.isdir(settings.SENDFILE_ROOT):
            os.makedirs(settings.SENDFILE_ROOT)
        path = os.path.join(settings.SENDFILE_ROOT, self.Regex.macro_filename(procname, version, revision))
        if not os.path.isfile(path):
            procedure_version = get_object_or_404(models.ProcedureVersion, procedure__version=version,
                                                  procedure__name=procname.replace('_', '.'), commit__revision=revision)
            with xlsxwriter.Workbook(path) as workbook:
                worksheet = workbook.add_worksheet()
                macro_headers = ("name", "path", "count_calls",)
                headers = macro_headers
                mapping_headers = dict((h, h,) for h in headers)
                mapping_headers.update({
                    "name": "Name",
                    "path": "Path",
                    "count_calls": "Calls"
                })
                mapping_data = dict((h, str,) for h in headers)
                format_ = workbook.add_format({'bold': True})
                for col, header, in enumerate(headers):
                    worksheet.write(0, col, mapping_headers[header], format_)
                for row, macro, in enumerate(procedure_version.data["macros"]):
                    col = 0
                    for header in macro_headers:
                        data = macro[header]
                        worksheet.write(row + 1, col, mapping_data[header](data))
                        col += 1


xlsx_backend = XLSXBackend()
