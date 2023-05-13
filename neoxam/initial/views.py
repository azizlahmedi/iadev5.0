# -*- coding: utf-8 -*-

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.shortcuts import render

from neoxam.initial import backends, consts


def handle_home(request):
    commits = backends.initialcommitbackend.get_initial_commits(consts.VERSION)
    paginator = Paginator(commits, consts.PAGINATION)
    page = request.GET.get('page')
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)

    return render(request, 'initial/commits.html', {
        'nav': 'commits',
        'commits': records,
    })
