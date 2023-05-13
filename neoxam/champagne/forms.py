# -*- coding: utf-8 -*-
import re

from crispy_forms.helper import FormHelper
from django.forms import ModelForm, ValidationError
from neoxam.champagne import models

procedure_name_re = re.compile('procedure\s+([^\s]+)\s+', flags=re.IGNORECASE)


class CompilationForm(ModelForm):
    class Meta:
        model = models.Compilation
        fields = ['src']

    def __init__(self, *args, **kwargs):
        super(CompilationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3'
        self.helper.field_class = 'col-sm-9'

    def clean_src(self):
        fd = self.cleaned_data.get('src')
        if fd:
            raw_content = fd.read()
            fd.seek(0)
            try:
                content = raw_content.decode('latin1')
            except:
                raise ValidationError('latin1 expected')
            else:
                m = procedure_name_re.search(content)
                if not m:
                    raise ValidationError('failed to extract procedure name')
                self.cleaned_data['procedure_name'] = m.group(1).lower()
        return fd
