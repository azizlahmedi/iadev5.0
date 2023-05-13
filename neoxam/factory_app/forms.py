# -*- coding: utf-8 -*-
import fnmatch
import logging
import re

from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ValidationError
from neoxam.factory_app import models

log = logging.getLogger(__name__)


class BatchForm(forms.ModelForm):
    class Meta:
        model = models.Batch
        fields = ['name']

    procedure_names = forms.CharField(widget=forms.Textarea, help_text='A procedure per line or use comma as separator.')

    def __init__(self, *args, **kwargs):
        super(BatchForm, self).__init__(*args, **kwargs)
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
            procedure_name = procedure_name.strip().replace('_', '.')
            if procedure_name:
                if not procedure_re.match(procedure_name):
                    raise ValidationError('invalid procedure: %s' % procedure_name)
                procedure_list.add(procedure_name)
        if not procedure_list:
            raise ValidationError('at least one procedure required')
        self.cleaned_data['procedure_names'] = procedure_list
        return procedure_list


class CompileLegacyForm(forms.ModelForm):
    class Meta:
        model = models.CompileLegacyTask
        fields = ['schema_version', 'procedure_name', 'username']

    def clean_schema_version(self):
        schema_version = self.cleaned_data.get('schema_version')
        if schema_version and schema_version != 2009:
            raise ValidationError('not allowed')
        return schema_version

    def clean_procedure_name(self):
        procedure_name = self.cleaned_data.get('procedure_name')
        if procedure_name:
            procedure_name = procedure_name.lower().replace('_', '.').strip()
        return procedure_name

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            for allowed_username in models.CompileLegacyUser.objects.values_list('username', flat=True):
                if fnmatch.fnmatch(username, allowed_username):
                    return username
            log.error('%s not allowed to trigger legacy compilations', username)
            raise ValidationError('not allowed')
        return username
