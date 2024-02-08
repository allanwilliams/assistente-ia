from django import forms
from ajax_select.fields import AutoCompleteSelectField
from django.utils.html import format_html
from .models import Lembretes
from apps.core.helpers.fields import label_tooltip
from django_currentuser.middleware import  get_current_authenticated_user

class LembretesForm(forms.ModelForm):
    destinatario = AutoCompleteSelectField('users_lembretes',
                                       label='Destinatário lembrete',
                                       required=False,
                                       show_help_text=False)

    def __init__(self, *args, **kwargs):
        super(LembretesForm, self).__init__(*args, **kwargs)

        if self.fields.get('destinatario'):
            self.fields['destinatario'].label= label_tooltip('Destinatário', 'Caso não selecione um destinatário o lembrete será adicionado a você!')

        if self.fields.get('prioridade'):
            self.fields.get('prioridade').help_text=format_html(
                """
                    <ul style='list-style: none; padding-left:0'>
                        <li style='display:inline; margin-right: 10px;'><span class="fa fa-square text-green"></span> Baixa</li>
                        <li style='display:inline; margin-right: 10px;'><span class="fa fa-square text-yellow"></span> Media</li>
                        <li style='display:inline;'><span class="fa fa-square text-red"></span> Alta</li>
                    </ul>
                """
            )
        if 'instance' in kwargs: # pragma: no cover
            if kwargs.get('instance') and kwargs['instance'].criado_por != get_current_authenticated_user():
                for f in list(self.fields):
                    self.fields[f].disabled = True
    class Meta:
        model = Lembretes
        fields = [
            "titulo",
            "descricao",
            "destinatario",
            "url_solicitada",
            "data",
            "status",
            "prioridade",
            "lembrete_proprio",
            "documento",
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': 'vLargeTextField'})
        }
