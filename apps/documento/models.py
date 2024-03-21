from django.db import models, transaction
from apps.core.mixins import BaseModel
from apps.documento.choices import CHOICES_CHAT_AUTOR, CHAT_AUTOR_IA, CHOICES_TRANSCRICAO_TIPO, CHOICES_STATUS_TRANSCRICAO, STATUS_FILA_PROCESSAMENTO
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
import os
from apps.users.models import User
from apps.documento.utils import processar_transcricoes


processar_transcricoes(repeat=20)

class Chat(BaseModel):
    titulo = models.CharField('Titulo', max_length=255)
    documento = models.FileField('Documento', upload_to='documento_chat')
    ativo = models.BooleanField('Ativo', default=True)
    chatpdf_source_id = models.CharField('Chat PDF source id', max_length=255, blank=True, null=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_usuario',
        blank=True, null=True
    )
    
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

                # msg_inicial = 'Bem vindo ao Dede chat.'

                if response.status_code == 200:
                    instance.chatpdf_source_id = response.json()['sourceId']
                    instance.save()

                else:
                    msg_inicial = 'Houve um erro ao processar o PDF'
                    nova_mensagem = Mensagem(texto=msg_inicial, chat_id=instance.id, autor=CHAT_AUTOR_IA, criado_em=datetime.now())
                    nova_mensagem.save()

                # Apenas para Honoráios
                # if response.status_code == 200 and instance.chatpdf_source_id:
                #     from .utils import create_questions
                #     question = 'faca topicos com valor da causa, condecao honorario, certidao transito julgado, comprimento de sentenca'
                #     CQ = create_questions(chat=instance.id,texto=question,autor=CHAT_AUTOR_IA,not_save = True)

               
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
    is_favorito = models.BooleanField('Favorito por usuário',default=False)

    def __str__(self) -> str:
        return f'{self.chat} - {self.get_autor_display()}'
    
    class Meta:
        verbose_name_plural = 'Mensagens'

class MediaTranscricao(BaseModel):
    titulo = models.CharField('Titulo', max_length=255,blank=True,null=True)
    arquivo = models.FileField('Arquivo', upload_to='arquivo_transcricao')
    legenda = models.FileField('Legenda', upload_to='legenda_transcricao',blank=True,null=True)
    tipo = models.IntegerField("Tipo",choices=CHOICES_TRANSCRICAO_TIPO)
    ativo = models.BooleanField('Ativo', default=True)
    chat = models.ForeignKey(
        Chat,
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_chat',
        blank=True,null=True
    )
    diarizacao = models.TextField("Diarização",blank=True,null=True)
    transcricao = models.TextField("Transcrição",blank=True,null=True)
    status = models.IntegerField('Status', choices=CHOICES_STATUS_TRANSCRICAO, default=STATUS_FILA_PROCESSAMENTO)

    def __str__(self):
        return f'{self.titulo}'


class Transcricao(BaseModel):
    media_transcricao = models.ForeignKey(
        MediaTranscricao,
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_media_transcricao',
    )
    texto = models.CharField("Texto",max_length=500)
    tempo_inicial = models.CharField("Tempo inicial",max_length=12)
    tempo_inicial_segundos = models.IntegerField("Tempo inicial em segundos", default=0)
    tempo_final = models.CharField("Tempo final",max_length=12)
    speaker = models.CharField("Speaker",max_length=255, blank=True, null=True)
    cor_speaker = models.CharField('Cor do Speaker', max_length=50, default="#0000FF")

    class Meta:
        ordering = ['id',]

    def __str__(self):
        return f'{self.media_transcricao.titulo}'