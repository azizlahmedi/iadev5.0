# -*- coding: utf-8 -*-
import logging
import os
import time

from django.http.response import HttpResponse
from django.shortcuts import render, redirect

from neoxam.delivery import forms, settings
from neoxam.delivery.backends import DeliveryBackend

log = logging.getLogger(__name__)


def handle_home(request):
    return redirect('delivery-new-delivery')


def handle_new_delivery(request):
    errors = []
    if request.method == 'POST':
        form = forms.DeliveryForm(request.POST)
        if form.is_valid():
            procedure_names = form.cleaned_data['procedure_names']
            repository = form.cleaned_data['repository']
            tar_gz_path = os.path.join(settings.DELIVERY_ROOT, 'delivery-%d.tar.gz' % int(time.time() * 1000))
            errors = DeliveryBackend().create_delivery(tar_gz_path, repository, procedure_names)
            if not errors:
                with open(tar_gz_path, 'rb') as f:
                    data = f.read()
                response = HttpResponse(data, content_type='application/gzip')
                response['Content-Disposition'] = "attachment; filename={0}".format(os.path.basename(tar_gz_path))
                response['Content-Length'] = os.path.getsize(tar_gz_path)
                return response
    else:
        form = forms.DeliveryForm()
    return render(request, 'delivery/new.html', {
        'nav': 'new',
        'form': form,
        'errors': errors,
    })


def handle_download(request, path):
    response = HttpResponse(mimetype='application/force-download')  # mimetype is replaced by content_type for django 1.7
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
