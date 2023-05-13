from crispy_forms.helper import FormHelper
from django import forms

VERSION_CHOICES = (
#    ("GP710", _("GP710")),
    ("GP2009", _("GP2009")),
    ("GP2016", _("GP2016")),
    ("GP2006", _("GP2006")))

class CrRemoverForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(CrRemoverForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-1'
        self.helper.field_class = 'col-sm-7'

    version = forms.ChoiceField(choices=VERSION_CHOICES,
                                label="Version") #CharField(label="Version")
    path = forms.CharField(label="Vms Path",
                           help_text="Example: MAG/6C0099.ME0")