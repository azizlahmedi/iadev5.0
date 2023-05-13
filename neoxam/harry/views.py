# -*- coding: utf-8 -*-
import json
import logging

from django.shortcuts import render, redirect
from neoxam.harry import forms, settings

from delia_mlg.services import create_services

log = logging.getLogger(__name__)


def handle_home(_request):
    return redirect('harry-json')


def process_json(json_untranslated):
    data = {}
    with open(json_untranslated.file.path, 'r', encoding='utf-8') as fd:
        for lang, lang_data in json.load(fd).items():
            for procedure_name, msgids in lang_data.items():
                if procedure_name not in data:
                    data[procedure_name] = set()
                data[procedure_name].update(msgids)
    services = create_services(settings.SETTINGS)
    services.source_backend.update_procedures(data.keys())
    for procedure_name, msgids in data.items():
        services.append_msgids(services.translation_backend_redis, procedure_name, msgids)
        services.translate_all_po(services.translation_backend_redis, procedure_name)
    services.source_backend.commit_procedures(data.keys(), username=json_untranslated.username)


def handle_json(request):
    if request.method == 'POST':
        form = forms.JsonUntranslatedForm(request.POST, request.FILES)
        if form.is_valid():
            json_untranslated = form.save()
            process_json(json_untranslated)
            return render(request, 'harry/json_done.html')
    else:
        form = forms.JsonUntranslatedForm()
    return render(request, 'harry/json.html', {
        'nav': 'json',
        'form': form,
    })
