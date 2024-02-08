from django.db import models
from apps.core.mixins import BaseModel
from django_currentuser.middleware import get_current_user
from django.utils.html import format_html
from apps.users.models import User
from .choices import (
    CHOICE_PRIORIDADE, 
    CHOICES_STATUS,
    STATUS_PENDENTE,
    PRIORIDADE_BAIXA
)

class Lembretes(BaseModel):
    cols = {
        'titulo': 2,
        'descricao': 12,
        'destinatario': 3,
        'data_hora': 3,
        'data': 2,
        'status': 4,
        'prioridade': 2
    }

    titulo = models.CharField('Titulo', max_length=255) 
    
    descricao = models.TextField('Descrição',null=True, blank=True)
    
    destinatario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='%(class)s_destinatario',
        blank=True,
        null=True,
        verbose_name='Destinatário'
    )

    url_solicitada = models.CharField('URL', max_length=500,null=True, blank=True) 

    data = models.DateField('Data', null=True, blank=True)

    status = models.IntegerField('Status', choices=CHOICES_STATUS, null=True, blank=True)

    prioridade = models.IntegerField('Prioridade', choices=CHOICE_PRIORIDADE, default=PRIORIDADE_BAIXA)

    lembrete_proprio = models.BooleanField('Lembrete próprio', default=False)

    documento = models.FileField(upload_to='lembretes', null=True, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.titulo, self.destinatario)
    
    def verifica_origem(self):
        return 'Recebido' if Lembretes.objects.filter(id=self.pk, destinatario__id=get_current_user().id).exists() else 'Enviado'

    verifica_origem.short_description = format_html('<div class="text"> <a href="#">Origem</a></div>')

    def get_origem(self):
        return self.criado_por.name.upper()

    get_origem.short_description = format_html('<div class="text"> <a href="#">De</a></div>')

    def get_destino(self):
        return self.destinatario.name.upper()

    get_destino.short_description = format_html('<div class="text"> <a href="#">Para</a></div>')
    

    def save(self):
        if not self.id:
            if not self.destinatario:
                self.destinatario = get_current_user()
                self.lembrete_proprio = True
            elif self.destinatario == get_current_user():
                self.lembrete_proprio = True

            if not self.status:
                self.status = STATUS_PENDENTE

        super(Lembretes, self).save(force_insert=False, force_update=False, using=None, update_fields=None)

    class Meta:
        verbose_name = 'Lembrete'
        verbose_name_plural = 'Lembretes'