from django.db import models
from apps.core.mixins import BaseModel
from apps.documento.choices import CHOICES_CHAT_AUTOR, CHAT_AUTOR_IA
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
import os

class Chat(BaseModel):
    titulo = models.CharField('Titulo', max_length=255)
    documento = models.FileField('Documento', upload_to='documento_chat')
    ativo = models.BooleanField('Ativo', default=True)
    chatpdf_source_id = models.CharField('Chat PDF source id', max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.id}'


@receiver(post_save, sender=Chat)
def criar_mensagens_chat(sender, instance, **kwargs):

    if instance and not instance.chatpdf_source_id:
        ROOT = os.path.abspath(os.path.dirname(f'media/documento_chat'))
        file_path = '{}/{}'.format(ROOT, instance.documento)
    
        try:
            with open(file_path, 'rb') as file:
            
                files = [
                    ('file', ('file', file, 'application/octet-stream'))
                ]
                headers = {
                    'x-api-key': 'sec_16KMXQwy0VcwkGz7xYuDY9PxWGGgsHM6'
                }

                response = requests.post(
                    'https://api.chatpdf.com/v1/sources/add-file', headers=headers, files=files)

                msg_inicial = 'Bem vindo ao dede chat. Faça a primeira pergunda.'

                if response.status_code == 200:
                    instance.chatpdf_source_id = response.json()['sourceId']
                    instance.save()
                else:
                    msg_inicial = 'Houve um erro ao processar o PDF'


                nova_mensagem = Mensagem(texto=msg_inicial, chat_id=instance.id, autor=CHAT_AUTOR_IA, criado_em=datetime.now())
                nova_mensagem.save()
        except Exception as e:
            print('erro', e)


class Mensagem(BaseModel):
    texto = models.TextField('mensagem')
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='%(class)s_chat',
    )
    autor = models.IntegerField('Autor', choices=CHOICES_CHAT_AUTOR)

    def __str__(self) -> str:
        return f'{self.chat} - {self.get_autor_display()}'
    
    class Meta:
        verbose_name_plural = 'Mensagens'

