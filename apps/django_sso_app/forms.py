from django import forms
from django.contrib.auth import (
    get_user_model, password_validation,
)
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import requests


UserModel = get_user_model()

class AdminPasswordChangeForm(forms.Form):
    message_password_didnt_match = 'The two password fields didn’t match.'
    """
    A form used to change the password of a user in the admin interface.
    """
    error_messages = {
        'password_mismatch': _(message_password_didnt_match),
        '[invalid]currentPassword': _("Your old password was entered incorrectly. Please enter it again."),
    }
    required_css_class = 'required'
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )

    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'autofocus': True}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password1',_(self.message_password_didnt_match))
            self.add_error('password2',_(self.message_password_didnt_match))
            raise ValidationError("Senhas não conferem")
        
        if settings.FUSIONAUTH_HOST and settings.FUSIONAUTH_USER_API_KEY:
            api_url = settings.FUSIONAUTH_HOST + 'api/user/change-password'
            data_user = { "loginId": self.user.email, "currentPassword": old_password, "password": password1 }
            headers = { 'Content-Type': 'application/json', 'Authorization': settings.FUSIONAUTH_USER_API_KEY }
            response = requests.post(url=api_url,json=data_user,headers=headers)
            if response.status_code != 200:
                self.handle_erros(response.json())
                raise ValidationError("Senhas não conferem")
        

    def save(self, commit=True):
        return self.user

    def handle_erros(self,data):
        for erros_type in data:
            errors = data.get(erros_type)
            for error in errors:
                messages = errors.get(error)
                for message in messages:
                    self.add_error('old_password',message.get('message'))
    @property
    def changed_data(self):
        data = super().changed_data
        for name in self.fields:
            if name not in data:
                return []
        return ['password']
