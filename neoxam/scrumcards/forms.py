# -*- coding: utf-8 -*-
from crispy_forms.helper import FormHelper
from django import forms

from neoxam.scrumcards.backend import backend

from neoxam.scrumcards.exceptions import NoSuchSprint


class CardForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CardForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3'
        self.helper.field_class = 'col-sm-9'

    sprint_id = forms.IntegerField(label='Sprint ID', min_value=0)
    blank_cards = forms.IntegerField(label='Blank Cards', min_value=0, initial=0)

    def clean_sprint_id(self):
        sprint_id = self.cleaned_data.get('sprint_id')
        if sprint_id:
            try:
                self.cleaned_data['cards'] = backend.get(sprint_id)
            except NoSuchSprint:
                raise forms.ValidationError('Sprint does not exist.')
        return sprint_id
