# -*- coding: utf-8 -*-
import re

from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ValidationError

from neoxam.delivery import models


class DeliveryForm(forms.Form):
    repository = forms.ModelChoiceField(queryset=models.Repository.objects.all())
    procedure_names = forms.CharField(widget=forms.Textarea, help_text='A procedure per line or use comma as separator.')

    def __init__(self, *args, **kwargs):
        super(DeliveryForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3'
        self.helper.field_class = 'col-sm-9'

    def clean_procedure_names(self):
        procedure_names = self.cleaned_data.get('procedure_names')
        if not procedure_names:
            return procedure_names
        procedure_re = re.compile('^[a-z0-9]+(\.[a-z0-9]+)*$')
        procedure_list = set()
        for procedure_name in procedure_names.replace('\r', '').replace('\n', ',').replace('\t', '').lower().split(','):
            procedure_name = procedure_name.strip()
            if procedure_name:
                if not procedure_re.match(procedure_name):
                    raise ValidationError('invalid procedure: %s' % procedure_name)
                procedure_list.add(procedure_name)
        if not procedure_list:
            raise ValidationError('at least one procedure required')
        self.cleaned_data['procedure_names'] = procedure_list
        return procedure_list
