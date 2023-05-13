# -*- coding: utf-8 -*-
import logging

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from neoxam.champagne import models, consts, forms, clients

log = logging.getLogger(__name__)


def handle_home(request):
    return redirect('champagne-compilations')


def clean_patterns(request):
    return [p for p in request.POST.getlist('patterns') if p in dict(consts.PATTERN_CHOICES)]


def handle_new(request):
    if request.method == 'POST':
        form = forms.CompilationForm(request.POST, request.FILES)
        if form.is_valid():
            compilation = form.save(commit=False)
            with transaction.atomic():
                compilation.procedure_name = form.cleaned_data['procedure_name']
                compilation.patterns = ','.join(clean_patterns(request))
                compilation.save()
                clients.compile_async(compilation)
            return redirect('champagne-compilations')
    else:
        form = forms.CompilationForm()
    return render(request, 'champagne/new.html', {
        'nav': 'new',
        'form': form,
        'patterns': consts.PATTERN_CHOICES,
    })


def handle_compilation(request, pk):
    compilation = get_object_or_404(models.Compilation, pk=pk)
    return render(request, 'champagne/compilation.html', {
        'compilation': compilation,
    })


def handle_compilations(request):
    compilation_list = models.Compilation.objects.order_by('-compiled_at')
    paginator = Paginator(compilation_list, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        compilations = paginator.page(page)
    except PageNotAnInteger:
        compilations = paginator.page(1)
    except EmptyPage:
        compilations = paginator.page(paginator.num_pages)
    return render(request, 'champagne/compilations.html', {
        'nav': 'compilations',
        'compilations': compilations,
    })
