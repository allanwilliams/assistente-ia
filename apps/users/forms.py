from django.contrib.auth import forms, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django import forms as django_forms
from ajax_select.fields import AutoCompleteSelectField

User = get_user_model()

class UserChangeForm(forms.UserChangeForm): # pragma: no cover
   
    class Meta(forms.UserChangeForm.Meta):
        model = User

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        cpf = cleaned_data.get("cpf")

        if cpf:
            if User.objects.filter(cpf=cpf).exclude(id=self.instance.id).exists():
                raise ValidationError("CPF já cadastrado")

class UserCreationForm(forms.UserCreationForm): # pragma: no cover

    error_message = forms.UserCreationForm.error_messages.update(
        {"duplicate_username": _("This username has already been taken.")}
    )

    class Meta(forms.UserCreationForm.Meta):
        model = User

    def clean_username(self):
        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])

class ImportarUsuariosForm(django_forms.Form):
    file = django_forms.FileField()

class PerfilForm(django_forms.ModelForm):
    municipio = AutoCompleteSelectField('municipios',
                                        label='Municipio',
                                        required=False,
                                        show_help_text=False)
    class Meta:
        model = User
        fields = (
            'name', 
            'cpf',
            'rg',
            'data_nascimento',
            'escolaridade',
            'telefone',
            'email_alternativo',
            'estado_civil',
            'nacionalidade',
            'estado',
            'foto',
            'cep',
            'endereco',
            'numero',
            'complemento',
            'bairro',
            'municipio',
            'nome_mae'
        )

    def __init__(self, *args, **kwargs):
        super(PerfilForm, self).__init__(*args, **kwargs)
        self.fields['data_nascimento'].widget.attrs['class'] = " vDateField"
        self.fields['cep'].widget.attrs['onblur'] = 'getCep(this)'

        for field in self.fields:
            if field != 'data_nascimento':
                self.fields[field].widget.attrs['class'] = " vTextField"
        
    def clean(self): # pragma: no cover
        cleaned_data = super().clean()

        cpf = cleaned_data.get("cpf")

        if cpf:
            if User.objects.filter(cpf=cpf).exclude(id=self.instance.id).exists():
                raise ValidationError("CPF já cadastrado")