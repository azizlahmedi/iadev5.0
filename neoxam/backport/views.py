# -*- coding: utf-8 -*-

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse

from neoxam.backport import backends
from neoxam.backport import consts as bp_consts
from neoxam.adltrack import models
import os


def handle_home(_):
    return redirect('backport-commits')


def handle_commits(request):
    record_list = backends.backport_backend.get_commits_without_update(bp_consts.FROM_VERSION, bp_consts.TO_VERSION)
    paginator = Paginator(record_list, bp_consts.PAGINATION)
    page = request.GET.get('page')
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)
    for record in records:
        record.patch = backends.backport_backend.get_patch(record.commit, bp_consts.TO_VERSION)
        
    return render(request, 'backport/commits.html', {
        'nav': 'commits',
        'records': records,
    })


def download_patch(_, revision):
    commit = get_object_or_404(models.Commit, revision=revision)
    patch = backends.backport_backend.get_patch(commit, bp_consts.TO_VERSION)
    response = HttpResponse(patch.patch_content, content_type="text/plain", charset='latin-1')
    response['Content-Disposition'] = 'attachment; filename="patch_{}.patch"'.format(revision)
    return response

def download_patched_file(_, revision):
    commit = get_object_or_404(models.Commit, revision=revision)
    patch = backends.backport_backend.get_patch(commit, bp_consts.TO_VERSION)
    patched_file_name = os.path.basename(patch.to_commit_path)
    response = HttpResponse(patch.file_patched, content_type="text/plain", charset='latin-1')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(patched_file_name)
    return response

def hide_commit(_, revision):
    commit = get_object_or_404(models.Commit, revision=revision)
    backends.backport_backend.hide_commit(commit, bp_consts.FROM_VERSION, bp_consts.TO_VERSION)
    return redirect('backport-commits')
