from django.db import models, transaction
from apps.core.mixins import BaseModel
from apps.documento.choices import (
    CHOICES_CHAT_AUTOR, 
    CHAT_AUTOR_IA, 
    CHOICES_TRANSCRICAO_TIPO, 
    CHOICES_STATUS_TRANSCRICAO, 
    STATUS_FILA_PROCESSAMENTO,
    CHOICES_STATUS_PDF,
    STATUS_OCR_DISPENSADO,
    STATUS_OCR_FILA,
    STATUS_OCR_PROCESSANDO,
    STATUS_PDF_FALHA_ENVIO
)
from datetime import datetime
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import requests
import os
from apps.users.models import User
from .utils import get_md5File, MartinhaUtils


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

    md5_hexdigit = models.CharField(max_length=64, blank=True, null=True)    
    status = models.IntegerField('Status', choices=CHOICES_STATUS_PDF, default=STATUS_OCR_DISPENSADO)
    visualizado = models.BooleanField('Visualizado', default=False)
    log_errors = models.TextField('Log errors', null=True, blank=True)
    is_martinha_processando = models.BooleanField('Processado pela Martinha',blank=True,null=True)

    def __str__(self) -> str:
        return f'{self.id}'
            
@receiver(post_save, sender=Chat)
def criar_mensagens_chat(sender, instance, created, **kwargs):

    ROOT = os.path.abspath(os.path.dirname(f'media/documento_chat'))
    file_path = '{}/{}'.format(ROOT, instance.documento)
    string_md5 = get_md5File(file_path)
    search_md5 = sender.objects.filter(criado_por=instance.criado_por,md5_hexdigit=string_md5,ativo=True)
    if instance and not instance.md5_hexdigit:
        if not search_md5:
            instance.md5_hexdigit = string_md5    
            instance.save()

    # if instance and not instance.status in [STATUS_OCR_FILA, STATUS_OCR_PROCESSANDO] and not instance.chatpdf_source_id:
    #     martinha_utils = MartinhaUtils(chat_id=instance.id)
    #     chatpdf_source_id = martinha_utils.enviar_arquivo_para_chatpdf()

    #     if chatpdf_source_id:
    #         instance.chatpdf_source_id = chatpdf_source_id
    #         instance.save()
    #     else:
    #         instance.status = STATUS_PDF_FALHA_ENVIO
    #         instance.save()
            

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
    md5_hexdigit = models.CharField(max_length=64, blank=True, null=True)
    visualizado = models.BooleanField('Visualizado', default=False)
    is_tanaka_processando = models.BooleanField('Processado pelo tanaka',blank=True,null=True)

    def __str__(self):
        return f'{self.titulo}'

@receiver(post_save, sender=MediaTranscricao)
def criar_transcricao(sender, instance, created, **kwargs):
    
    ROOT = os.path.abspath(os.path.dirname(f'media/arquivo_transcricao'))
    file_path = '{}/{}'.format(ROOT, instance.arquivo)
    string_md5 = get_md5File(file_path)
    search_md5 = sender.objects.filter(criado_por=instance.criado_por,md5_hexdigit=string_md5,ativo=True)
    if instance and not instance.md5_hexdigit:
        if not search_md5:
            instance.md5_hexdigit = string_md5    
            instance.save()
class Transcricao(BaseModel):
    media_transcricao = models.ForeignKey(
        MediaTranscricao,
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_media_transcricao',
    )
    texto = models.TextField("Texto")
    tempo_inicial = models.CharField("Tempo inicial",max_length=12)
    tempo_inicial_segundos = models.IntegerField("Tempo inicial em segundos", default=0)
    tempo_final = models.CharField("Tempo final",max_length=12)
    speaker = models.CharField("Speaker",max_length=255, blank=True, null=True)
    cor_speaker = models.CharField('Cor do Speaker', max_length=50, default="#0000FF")
    is_favorito = models.BooleanField('Favorito por usuário', default=False)
    is_vetado = models.BooleanField('Vetado pelo usuário', default=False)

    class Meta:
        ordering = ['id',]

    def __str__(self):
        return f'{self.media_transcricao.titulo}'
    

class AssistentePerfil(BaseModel):
    openia_assistente_id = models.CharField('Openia assistente id', max_length=255, blank=True, null=True)
    nome = models.CharField('Nome', max_length=255, blank=True, null=True)
    apresentacao = models.TextField('Apresentação', blank=True, null=True)
    avatar = models.FileField('Avatar', upload_to='assistente_avatar', null=True, blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    grupo_permissao = models.CharField('Grupo Permissão', max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.nome}'

class AssistenteTopico(BaseModel):
    openia_thread_id = models.CharField('Thread id', max_length=255, blank=True, null=True)
    ativo = models.BooleanField('Ativo', default=True)
    assistente = models.ForeignKey(
        AssistentePerfil,
        on_delete=models.CASCADE,
        related_name='%(class)s_assistente',
        null=True, blank=True
    )

    def __str__(self):
        return f'{self.openia_thread_id}'


class AssistenteMensagem(BaseModel):
    texto = models.TextField('mensagem')

    topico = models.ForeignKey(
        AssistenteTopico,
        on_delete=models.CASCADE,
        related_name='%(class)s_topico',
    )
    autor = models.IntegerField('Autor', choices=CHOICES_CHAT_AUTOR)

