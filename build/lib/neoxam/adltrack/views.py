# -*- coding: utf-8 -*-
import os
import re

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from sendfile import sendfile

from neoxam.adltrack import models, consts, backends


def handle_home(request):
    return redirect('adltrack-commits')


def handle_procedures(request):
    procedure_list = models.Procedure.objects.order_by('-version', 'name')
    paginator = Paginator(procedure_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        procedures = paginator.page(page)
    except PageNotAnInteger:
        procedures = paginator.page(1)
    except EmptyPage:
        procedures = paginator.page(paginator.num_pages)
    return render(request, 'adltrack/procedures.html', {
        'nav': 'procedures',
        'procedures': procedures,
    })


def handle_procedures_analysis(request):
    procedure_version_list = models.ProcedureVersion.objects.filter(head=True, analyzed=False).order_by('-commit__revision', 'procedure__name', '-procedure__version')
    paginator = Paginator(procedure_version_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        procedure_versions = paginator.page(page)
    except PageNotAnInteger:
        procedure_versions = paginator.page(1)
    except EmptyPage:
        procedure_versions = paginator.page(paginator.num_pages)
    return render(request, 'adltrack/procedures_analysis.html', {
        'nav': 'procedures-analysis',
        'procedure_versions': procedure_versions,
    })


def handle_procedure(request, version, name):
    procedure = get_object_or_404(models.Procedure, version=version, name=name)
    procedure_version_list = procedure.procedure_versions.select_related('commit').order_by('-commit__revision')
    paginator = Paginator(procedure_version_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        procedure_versions = paginator.page(page)
    except PageNotAnInteger:
        procedure_versions = paginator.page(1)
    except EmptyPage:
        procedure_versions = paginator.page(paginator.num_pages)
    return render(request, 'adltrack/procedure.html', {
        'procedure': procedure,
        'procedure_versions': procedure_versions,
    })


def handle_commits(request):
    commit_list = models.Commit.objects.order_by('-revision')
    paginator = Paginator(commit_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        commits = paginator.page(page)
    except PageNotAnInteger:
        commits = paginator.page(1)
    except EmptyPage:
        commits = paginator.page(paginator.num_pages)
    return render(request, 'adltrack/commits.html', {
        'nav': 'commits',
        'commits': commits,
    })


def handle_commit(request, revision):
    commit = get_object_or_404(models.Commit, revision=revision)
    procedure_version_list = commit.procedure_versions.select_related('procedure').order_by(
        '-procedure__version',
        'procedure__name',
    )
    paginator = Paginator(procedure_version_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        procedure_versions = paginator.page(page)
    except PageNotAnInteger:
        procedure_versions = paginator.page(1)
    except EmptyPage:
        procedure_versions = paginator.page(paginator.num_pages)
    return render(request, 'adltrack/commit.html', {
        'commit': commit,
        'procedure_versions': procedure_versions
    })


def handle_procedure_version(request, version, name, revision):
    procedure_version = get_object_or_404(models.ProcedureVersion, procedure__version=version, procedure__name=name,
                                          commit__revision=revision)
    return render(request, 'adltrack/procedure_version.html', {
        'procedure_version': procedure_version,
    })


def handle_tops(request):
    procedure_versions = list(models.ProcedureVersion.objects.filter(head=True, analyzed=True).select_related('commit', 'procedure'))
    procedure_versions_tokens = sorted(procedure_versions, key=lambda x: -x.data['count_tokens'])[:50]
    procedure_versions_macros = sorted(procedure_versions, key=lambda x: -len(x.data['macros']))[:50]
    return render(request, 'adltrack/tops.html', {
        'procedure_versions_tokens': procedure_versions_tokens,
        'procedure_versions_macros': procedure_versions_macros,
        'nav': 'tops',
    })


def handle_sendfile(request, filename):
    def _process_commit(basename):
        regex_commit_filename = re.compile(backends.xlsx_backend.Regex.COMMIT)
        match = regex_commit_filename.fullmatch(basename)
        if match is not None:
            revision, = match.groups()
            backends.xlsx_backend.process_commit(int(revision))

    def _process_macro(basename):
        regex_macro_filename = re.compile(backends.xlsx_backend.Regex.MACRO)
        match = regex_macro_filename.fullmatch(basename)
        if match is not None:
            procname, version, revision, = match.group(1, 3, 4)
            backends.xlsx_backend.process_macro(procname, int(version), int(revision))

    basename = os.path.basename(filename)
    _process_commit(basename)
    _process_macro(basename)
    return sendfile(request, os.path.join(settings.SENDFILE_ROOT, basename), attachment=True, attachment_filename=basename)
