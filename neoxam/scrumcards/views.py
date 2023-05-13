# -*- coding: utf-8 -*-
from django.shortcuts import render

from neoxam.scrumcards.backend import empty_card
from neoxam.scrumcards import forms


def handle_home(request):
    if request.method == 'POST':
        form = forms.CardForm(request.POST)
        if form.is_valid():
            cards = form.cleaned_data['cards']
            for i in range(form.cleaned_data['blank_cards']):
                cards.append(empty_card)
            return render(request, 'scrumcards/print.html', {
                'cards': cards,
            })
    else:
        form = forms.CardForm()
    return render(request, 'scrumcards/index.html', {'form': form})
