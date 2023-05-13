# -*- coding: utf-8 -*-
from django.shortcuts import render


def handle_home(request):
    return render(request, 'commons/home.html')
