from django import forms


class LoginForm(forms.Form):
    ldap_username = forms.CharField(
        label="Jira user name:")
    ldap_password = forms.CharField(
        label="Jira password:",
        widget=forms.PasswordInput)
