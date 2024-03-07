from django.db import models
from apps.core.mixins import BaseModel
from apps.documento.choices import CHOICES_CHAT_AUTOR, CHAT_AUTOR_IA, CHOICES_TRANSCRICAO_TIPO
from datetime import datetime, timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
from apps.users.models import User
from django.core.files.storage import FileSystemStorage
from pydub import AudioSegment
import os
import subprocess
from openai import OpenAI
import pdfkit
from apps.documento.utils import process_audio, get_diarizations, get_speaker
import json

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

    def __str__(self):
        return f'{self.titulo}'

@receiver(post_save, sender=MediaTranscricao)
def transcrever_audio_media_transcricao(sender, instance, **kwargs):
    def convert_to_time(number, microseconds=False):
        delta_tempo = timedelta(seconds=number)
        time = "{:02}:{:02}:{:02}".format(delta_tempo.seconds // 3600, (delta_tempo.seconds % 3600) // 60, delta_tempo.seconds % 60)
        if microseconds:
            microssegundos_limitados = min(delta_tempo.microseconds // 1000, 999)
            time = "{}.{:03}".format(time, microssegundos_limitados)
        return time

    if instance and not instance.chat and instance.ativo:
        ROOT = os.path.abspath(os.path.dirname(f'media/arquivo_transcricao'))
        ROOT_LEGENDA = os.path.abspath(os.path.dirname(f'media/legenda_transcricao'))
        ROOT_PDF = os.path.abspath(os.path.dirname(f'media/documento_chat'))
        
        file_path = '{}/{}'.format(ROOT, instance.arquivo)
    
        try:
            arquivo_file = instance.arquivo
            filename_audio = str(arquivo_file.name).split('.')[-2]
            path_media_legenda = f'{ROOT_LEGENDA}/{filename_audio}.vtt'
            path_media_audio = f'{ROOT}/{filename_audio}.wav'
            path_media_pdf = f'{ROOT_PDF}/{filename_audio}.pdf'
            
            # converte arquivo em wav
            path_media_audio = process_audio(file_path)
            
            # converte arquivo wav em mp3
            convert = AudioSegment.from_file(file_path)
            audio_file = convert.export('exemplo.mp3', format="mp3")
            
            
            if audio_file:
                # envia arquiv para OpenAI
                client = OpenAI(api_key="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")
                transcricao = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file, 
                    response_format="verbose_json"
                )

                if transcricao:
                    diarization = get_diarizations(path_media_audio)
                    texto_total = ""
                    with open(path_media_legenda, 'w') as vtt:
                        vtt.write('WEBVTT\n')
                        
                        for t in transcricao.segments:
                            start = convert_to_time(t.get('start'), True)
                            end = convert_to_time(t.get('end'), True)
                            text = t.get('text')

                            vtt.write(f'{start} --> {end}\r')
                            vtt.write(f'{str(text).strip()}\r')

                            texto_total += f'{start} - {end}</br>'
                            texto_total += f'{text}</br>'

                            dict_transcricao = {
                                'media_transcricao': instance,
                                'texto': text,
                                'tempo_inicial': start,
                                'tempo_final': end,
                                'speaker': get_speaker(diarization,t.get('start'),t.get('end'))
                            }
                            transcricao_new = Transcricao(**dict_transcricao)
                            transcricao_new.save()

                        instance.legenda = f'{filename_audio}.vtt'
                        instance.diarizacao = diarization
                        transcricao_obj = {
                            "segments": transcricao.segments,
                        }
                        instance.transcricao = json.dumps(transcricao_obj)
                            
                    vtt.close()
                    
                    pdfkit.from_string(texto_total, path_media_pdf)

                    dict_chat = {
                        'titulo': filename_audio,
                        'documento': f'{filename_audio}.pdf',
                        'ativo': True,
                        'usuario': instance.criado_por,
                    }
                    
                    chat = Chat(**dict_chat)
                    chat.save()
                    
                    instance.chat = chat
                    instance.save()
        except Exception as e:
            print('erro', e)

class Transcricao(BaseModel):
    media_transcricao = models.ForeignKey(
        MediaTranscricao,
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_media_transcricao',
    )
    texto = models.CharField("Texto",max_length=500)
    tempo_inicial = models.CharField("Tempo inicial",max_length=12)
    tempo_final = models.CharField("Tempo final",max_length=12)
    speaker = models.CharField("Speaker",max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['id',]

    def __str__(self):
        return f'{self.media_transcricao.titulo}'