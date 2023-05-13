# -*- coding: utf-8 -*-
import json
import logging
import os
import shutil
import subprocess
import uuid

from django.db import transaction
from django.http.response import HttpResponse, StreamingHttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

#from factory.backends.base import untar, support_environ
from neoxam.eclipse import settings, forms, backends, consts, models
from neoxam.factory_app import clients as factory_clients
from neoxam.factory_app import consts as factory_consts
from neoxam.factory_app import services as factory_services
from neoxam.factory_app.models import Compiler

log = logging.getLogger(__name__)


def handle_home(request):
    return HttpResponse('OK')


def compile(compile_uid, support_home, checkout, schema_version, procedure_name, json_output, on_success=None):
    env = support_environ(support_home)
    publish_root = os.path.join(settings.PUBLISH_ROOT, compile_uid)
    publish_url = settings.PUBLISH_URL + compile_uid
    os.makedirs(publish_root)
    stream = 'stdout'
    stdout = subprocess.PIPE
    stderr = subprocess.STDOUT
    command = [
        'deliac',
        '-p', os.path.join(checkout, 'gp%d' % schema_version),
        '-o', publish_root,
        '-n', procedure_name,
        '-m',
    ]
    if json_output:
        command.extend(['--error-format', 'json'])
        stream = 'stderr'
        stdout = subprocess.DEVNULL
        stderr = subprocess.PIPE
    process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env)
    for line in getattr(process, stream):
        yield line.decode('utf-8', 'replace').replace(checkout + os.path.sep, '')
    code = process.wait()
    success = code == 0
    if success and on_success is not None:
        on_success()
    urls = [publish_url + '/' + bn for bn in os.listdir(publish_root)]
    yield 'JSON: ' + json.dumps({'success': success, 'urls': urls})


class PostActionStreamingHttpResponse(StreamingHttpResponse):
    def __init__(self, post_actions, *args, **kwargs):
        self.post_actions = post_actions
        super(PostActionStreamingHttpResponse, self).__init__(*args, **kwargs)
        self['X-Accel-Buffering'] = 'no'

    def close(self):
        for post_action in self.post_actions:
            post_action()
        super(PostActionStreamingHttpResponse, self).close()


def has_json_output(request):
    return request.GET.get('format', '') == 'json'


@csrf_exempt
@require_POST
def handle_compile(request):
    form = forms.CompileForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest(json.dumps(form.errors))
    # Parameters
    schema_version = form.cleaned_data['schema_version']
    procedure_name = form.cleaned_data['procedure_name']
    compiler_version = form.cleaned_data['compiler_version']
    compiler, created = Compiler.objects.get_or_create(version=compiler_version, defaults={'enabled': False})
    compile_uid = str(uuid.uuid1())
    temp = os.path.join(settings.TMP, compile_uid)
    os.makedirs(temp)
    checkout = os.path.join(temp, 'checkout')
    bundle_path = os.path.join(temp, procedure_name.replace('.', '_') + '.tar.gz')
    with open(bundle_path, 'wb') as fd:
        for chunk in form.cleaned_data['sources'].chunks():
            fd.write(chunk)
    untar(bundle_path, checkout)
    with compiler.lock() as compiler_host:
        support_home = compiler_host.support_home
        factory_services.create_services(schema_version).ensure_compiler(compiler_version, support_home)
    streaming_content = compile(compile_uid, support_home, checkout, schema_version, procedure_name, has_json_output(request))
    post_actions = [lambda: shutil.rmtree(temp), ]
    return PostActionStreamingHttpResponse(post_actions, streaming_content)


@csrf_exempt
@require_POST
def handle_deliver(request):
    form = forms.DeliverForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest(json.dumps(form.errors))
    schema_version = form.cleaned_data['schema_version']
    procedure_name = form.cleaned_data['procedure_name']
    compiler_version = form.cleaned_data['compiler_version']
    compiler, created = Compiler.objects.get_or_create(version=compiler_version, defaults={'enabled': False})
    compile_uid = str(uuid.uuid1())
    temp = os.path.join(settings.TMP, compile_uid)
    os.makedirs(temp)
    checkout = os.path.join(temp, 'checkout')
    bundle_path = os.path.join(temp, procedure_name.replace('.', '_') + '.tar.gz')
    with open(bundle_path, 'wb') as fd:
        for chunk in form.cleaned_data['sources'].chunks():
            fd.write(chunk)
    untar(bundle_path, checkout)
    excludes = ('mv.py', 'project.cfg')
    rel_paths = []
    server = os.path.join(temp, 'server')
    for root, dirs, files in os.walk(checkout):
        for bn in files:
            if bn not in excludes:
                rel_paths.append(os.path.join(root, bn).replace(checkout, '', 1).lstrip(os.path.sep))
    subversion_backend = backends.SubversionBackend()
    revision = subversion_backend.get_head_revision()
    subversion_backend.export(revision, server, rel_paths)
    command = ['diff', '-r', os.path.basename(checkout), os.path.basename(server)]
    for exclude in excludes:
        command.extend(['-x', exclude])
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT, cwd=temp, timeout=consts.DIFF_TIMEOUT)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp)

        def streaming_content(output):
            for line in output.decode('utf-8', 'replace').splitlines():
                yield line + '\n'
            yield 'synchronize your checkout\n'
            yield 'JSON: ' + json.dumps({'success': 0})

        return StreamingHttpResponse(streaming_content(e.output))
    with compiler.lock() as compiler_host:
        support_home = compiler_host.support_home
        factory_services.create_services(schema_version).ensure_compiler(compiler.version, support_home)
    on_success = lambda: factory_clients.compile(schema_version, procedure_name, revision, revision, priority=factory_consts.HIGH, force=True)
    streaming_content = compile(compile_uid, support_home, checkout, schema_version, procedure_name, has_json_output(request), on_success)
    post_actions = [lambda: shutil.rmtree(temp), ]
    return PostActionStreamingHttpResponse(post_actions, streaming_content)


@csrf_exempt
@require_POST
def handle_stats(request):
    with transaction.atomic():
        stats = models.Stats.objects.from_request(request)
    backends.get_elastic_backend().store(stats)
    return HttpResponse('OK')


def handle_runtime(request):
    data = []
    for runtime in models.Runtime.objects.filter(enabled=True).order_by('-release_date'):
        data.append({
            'version': runtime.version,
            'url': runtime.url,
            'release_date': runtime.release_date.isoformat(),
        })
    return HttpResponse(json.dumps(data))


@csrf_exempt
@require_POST
def handle_new_deliver_test(request):
    form = forms.DeliverTestForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseBadRequest(json.dumps(form.errors))
    schema_version = form.cleaned_data['schema_version']
    procedure_name = form.cleaned_data['procedure_name']
    procedure_test_name = form.cleaned_data['procedure_test_name']
    uuid4 = str(uuid.uuid4())
    bundle_path = os.path.join(settings.TMP, uuid4 + '.tar.gz')
    with open(bundle_path, 'wb') as fd:
        for chunk in form.cleaned_data['sources'].chunks():
            fd.write(chunk)
    with transaction.atomic():
        task = models.DeliverTestTask.objects.create(
            uuid=uuid4,
            schema_version=schema_version,
            procedure_name=procedure_name,
            procedure_test_name=procedure_test_name,
        )
    command = [
        'nohup',
        'neoxam',
        'deliver_test',
        '-i', str(task.pk),
        '-s', str(schema_version),
        '-n', procedure_name,
        '-t', procedure_test_name,
        '-b', bundle_path,
    ]
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, preexec_fn=os.setpgrp)
    return HttpResponse(json.dumps(task.as_json()))


def handle_deliver_test(request, pk):
    task = get_object_or_404(models.DeliverTestTask, pk=pk)
    return HttpResponse(json.dumps(task.as_json()))
