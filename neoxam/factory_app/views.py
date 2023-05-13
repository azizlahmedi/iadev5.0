# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import subprocess

import requests
import zipfile

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.http.response import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from neoxam.factory_app import models, consts, forms, clients, backends

log = logging.getLogger(__name__)


def handle_home(request):
    return redirect('factory-tasks')
    
    
    
    
import os
import zipfile
import shutil


import requests
from django.http import HttpResponse
from django.shortcuts import render

def handle_upload(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        comments = request.POST.get('comments')
        upload_files = request.FILES.getlist('uploadFiles')

        save_dir = os.path.join(os.path.dirname(__file__), 'tmp')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        else:
            shutil.rmtree(save_dir)
            os.makedirs(save_dir)

        for upload_file in upload_files:
            file_path = os.path.join(save_dir, upload_file.name)
            with open(file_path, 'wb') as f:
                for chunk in upload_file.chunks():
                    f.write(chunk)

        commit_result = svn_commit(save_dir, language, comments)

        shutil.rmtree(save_dir)

        if commit_result:
            response_msg = f'Upload successful and commit successful: {commit_result}'
        else:
            response_msg = 'Upload successful but commit failed'
        
        return HttpResponse(response_msg)

    return render(request, 'factory/upload-trad.html')


def svn_commit(directory, language, comments):
    os.chdir(directory)

    subprocess.run(['svn', 'add', '--force', '*'])

    svn_url = f'http://avalon.bams.corp:3180/svn/repos/gp/trunk/gp2009/adl/src/mlg/{language}'
    subprocess.run(['svn', 'commit', '-m', f'Commit {language}: {comments}', '--username', 'cis', '--password', 'Ntic2007', '--non-interactive', '--no-auth-cache', '--parents', '--trust-server-cert', '--force-log', svn_url])



def handle_trad(request):
    if request.method == 'POST':
        language = request.POST.get('language')
        procedure_names = request.POST.get('procedure_names')

        # Split procedure names by line breaks and commas
        procedure_names = procedure_names.strip().replace(',', '\n')
        procedure_names = [x.strip() for x in procedure_names.split('\n')]

        # Create a temporary directory to store the downloaded PO files
        tmp_dir = os.path.join(os.path.dirname(__file__), 'tmp')
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        else:
            # Delete all files in the tmp directory
            for filename in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, filename))

        # Download the PO files
        for procedure_name in procedure_names:
            full_procedure_name = f"{procedure_name}_{language}"
            url = f'http://avalon.bams.corp:3180/svn/repos/gp/trunk/gp2009/adl/src/mlg/{language}/{full_procedure_name}.po'
            response = requests.get(url, auth=('cis', 'Ntic2007'))
            if response.status_code == 200:
                with open(os.path.join(tmp_dir, f'{full_procedure_name}.po'), 'wb') as f:
                    f.write(response.content)
            elif response.status_code == 401:
                return HttpResponse('Authentication failed', status=401)
            elif response.status_code == 404:
                return HttpResponse(f'File not found: {full_procedure_name}.po', status=404)
            else:
                return HttpResponse(f'An error occurred while downloading {full_procedure_name}.po', status=500)

        # Create a zip file containing all the downloaded PO files
        zip_filename = os.path.join(tmp_dir, f'{language}.zip')
        with zipfile.ZipFile(zip_filename, 'w') as zip_file:
            for filename in os.listdir(tmp_dir):
                if filename.endswith('.po'):
                    zip_file.write(os.path.join(tmp_dir, filename), filename)

        # Serve the zip file as a response
        with open(zip_filename, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{language}.zip"'
            return response

    return render(request, 'factory/traduction.html')
    
    
    
    
    


def handle_tasks(request):
    task_list = models.Task.objects.all().select_related('procedure_revision__procedure', 'compiler').order_by(
        '-created_at')
    paginator = Paginator(task_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)
    return render(request, 'factory/tasks.html', {
        'nav': 'tasks',
        'tasks': tasks,
    })


def handle_task(request, pk):
    task = get_object_or_404(models.Task, pk=pk)
    return render(request, 'factory/task.html', {
        'task': task,
    })


def handle_batches(request):
    batch_list = models.Batch.objects.all().order_by('-created_at')
    paginator = Paginator(batch_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        batches = paginator.page(page)
    except PageNotAnInteger:
        batches = paginator.page(1)
    except EmptyPage:
        batches = paginator.page(paginator.num_pages)
    return render(request, 'factory/batches.html', {
        'nav': 'batches',
        'batches': batches,
    })


def handle_batch(request, pk):
    batch = get_object_or_404(models.Batch, pk=pk)
    tasks = models.Task.objects.filter(procedure_revision__batches=batch).order_by('procedure_revision')
    return render(request, 'factory/batch.html', {
        'batch': batch,
        'tasks': tasks,
    })


def handle_new_batch(request):
    if request.method == 'POST':
        form = forms.BatchForm(request.POST)
        if form.is_valid():
            head_revision = backends.SubversionBackend().get_head_revision()
            with transaction.atomic():
                batch = form.save()
            for procedure_name in form.cleaned_data['procedure_names']:
                procedure_revision = clients.compile(2016, procedure_name, head_revision, head_revision)
                batch.procedure_revisions.add(procedure_revision)
            return redirect('factory-batch', pk=batch.pk)
    else:
        form = forms.BatchForm()
    return render(request, 'factory/new_batch.html', {
        'nav': 'new-batch',
        'form': form,
    })


def handle_batch_retry(request, pk):
    batch = get_object_or_404(models.Batch, pk=pk)
    index = 2
    name = batch.name
    match = re.search(' #(\d+)$', batch.name)
    if match:
        name = name[:match.span()[0]]
        index = int(match.group(1)) + 1
    new_name = name + ' #%d' % index
    new_batch = models.Batch.objects.create(name=new_name)
    head_revision = backends.SubversionBackend().get_head_revision()
    for procedure_revision in batch.procedure_revisions.all():
        new_procedure_revision = clients.compile(procedure_revision.procedure.schema_version, procedure_revision.procedure.name, head_revision, head_revision, force=True)
        new_batch.procedure_revisions.add(new_procedure_revision)
    return redirect('factory-batch', pk=new_batch.pk)


def handle_compile_legacy_tasks(request):
    task_list = models.CompileLegacyTask.objects.all().order_by('-created_at')
    paginator = Paginator(task_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)
    return render(request, 'factory/compile_legacy_tasks.html', {
        'tasks': tasks,
        'nav': 'compile-legacy',
    })


def handle_compile_legacy_task(request, pk):
    task = get_object_or_404(models.CompileLegacyTask, pk=pk)
    return render(request, 'factory/compile_legacy_task.html', {
        'task': task,
    })


@csrf_exempt
@require_POST
def handle_compile_legacy(request):
    form = forms.CompileLegacyForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(json.dumps(form.errors))
    with transaction.atomic():
        task = form.save()
    command = [
        'nohup',
        'neoxam',
        'compile_legacy',
        '-i', str(task.pk),
        '-s', str(task.schema_version),
        '-n', task.procedure_name,
    ]
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, preexec_fn=os.setpgrp)
    return HttpResponse('OK')
