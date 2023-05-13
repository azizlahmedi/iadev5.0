# -*- coding: utf-8 -*-

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from .forms import CrRemoverForm
from neoxam.gpatcher import backends, models, settings

def handle_home(request):

    form = CrRemoverForm()
    return render(request, 'gpatcher/gpatcher.html', {'form': form})


def patch_source(request):

    if request.method == 'POST':

        form = CrRemoverForm(request.POST)

        if form.is_valid():

            version = form.cleaned_data["version"]
            path = form.cleaned_data["path"]

            try:
                backends.cr_remover(version, path)
                backends.add_new_record(request, version, path, True)
                return redirect('gpatcher-result')
            except Exception as e:
                print(e)
                backends.add_new_record(request, version, path, False)
                return redirect('gpatcher-result')

    return render(request, 'gpatcher/gpatcher.html', {'form': form})

def result(request):

    record_list = models.PatchRecord.objects.order_by('-time')

    paginator = Paginator(record_list, settings.PAGINATION)
    page = request.GET.get('page')
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)
        
    return render(request, 'gpatcher/result.html', {
        'nav': 'commits',
        'patch_records': records,
    })