# -*- coding: utf-8 -*-
from django import forms


class ActionForm(forms.Form):
    procedure_name = forms.CharField(max_length=255)
    compiler_version = forms.CharField(max_length=255)
    sources = forms.FileField()


class CompileForm(ActionForm):
    schema_version = forms.IntegerField()


class DeliverForm(ActionForm):
    schema_version = forms.IntegerField(min_value=2016)


class DeliverTestForm(forms.Form):
    schema_version = forms.IntegerField()
    procedure_name = forms.CharField(max_length=255)
    procedure_test_name = forms.CharField(max_length=255)
    sources = forms.FileField()
