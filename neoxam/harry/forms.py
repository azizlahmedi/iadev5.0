# -*- coding: utf-8 -*-
from crispy_forms.helper import FormHelper
from django import forms
from neoxam.harry import models


class JsonUntranslatedForm(forms.ModelForm):
    class Meta:
        model = models.JsonUntranslated
        fields = ['username', 'comment', 'file']

    def __init__(self, *args, **kwargs):
        super(JsonUntranslatedForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3'
        self.helper.field_class = 'col-sm-9'
