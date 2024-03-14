import requests
# from .models import Chat, Mensagem 
from apps.documento.choices import (
    CHAT_AUTOR_IA, 
    STATUS_PROCESSANDO_ARQUIVO,
    STATUS_FALHA_PROCESSAMENTO,
    STATUS_FAZENDO_TRANSCRICAO,
    STATUS_FALHA_TRANSCRICAO,
    STATUS_CONCLUIDO,
    STATUS_FILA_PROCESSAMENTO
)

from background_task import background

import subprocess
from django.core.files.storage import FileSystemStorage
from pydub import AudioSegment
from datetime import timedelta
from openai import OpenAI
import pdfkit
from config.settings import ROOT_DIR
from apps.documento import models
from background_task.models import CompletedTask


ROOT_MEDIA = f'{ROOT_DIR}/media'
ROOT_LEGENDA = f'{ROOT_DIR}/media/legenda_transcricao'
ROOT_PDF = f'{ROOT_DIR}/media/documento_chat'


def create_questions(*args, **kwargs):

    chat = kwargs['chat']
    texto = kwargs['texto']
    autor = kwargs['autor']
    not_save = kwargs.get('not_save')


    if not not_save:
        nova_msg = models.Mensagem(chat_id=chat, texto=texto, autor=autor)
        nova_msg.save()

    chatpdf_source_id = models.Chat.objects.get(pk=chat).chatpdf_source_id

    headers = {
        'x-api-key': 'sec_16KMXQwy0VcwkGz7xYuDY9PxWGGgsHM6',
        "Content-Type": "application/json",
    }

    data = {
        "referenceSources": True,
        'sourceId': chatpdf_source_id,
        'messages': [
            {
                'role': "user",
                'content': texto,
            }
        ]
    }

    response = requests.post(
        'https://api.chatpdf.com/v1/chats/message', headers=headers, json=data)

    resposta_chatpdf = models.Mensagem(chat_id=chat, texto='', autor=CHAT_AUTOR_IA)
    
    if response.status_code == 200:
        resposta_chatpdf.texto = response.json()['content']
    else:
        resposta_chatpdf.texto = 'Erro ao responder'

    resposta_chatpdf.save()
    return resposta_chatpdf


def convert_to_time(number, microseconds=False):
    delta_tempo = timedelta(seconds=number)
    time = "{:02}:{:02}:{:02}".format(delta_tempo.seconds // 3600, (delta_tempo.seconds % 3600) // 60, delta_tempo.seconds % 60)
    if microseconds:
        microssegundos_limitados = min(delta_tempo.microseconds // 1000, 999)
        time = "{}.{:03}".format(time, microssegundos_limitados)
    return time


def atualizar_status_transcricao(id, status):
    models.MediaTranscricao.objects.filter(pk=id).update(status=status)


def start_pipeline_transcricao(id):
    preparar_audio(id)


def preparar_audio(media_transcricao_id):
    instance = models.MediaTranscricao.objects.get(pk=media_transcricao_id)
    filename_audio = str(instance.arquivo.name).split('.')[-2].split('/')[1]
    path_media_audio = f'{ROOT_MEDIA}/{filename_audio}.wav'

    file_path = '{}/{}'.format(ROOT_MEDIA, instance.arquivo)
    
    print("<<<<<<<<<<<< PREPARANDO AUDIO >>>>>>>>>>>>")
    atualizar_status_transcricao(media_transcricao_id, STATUS_PROCESSANDO_ARQUIVO)

    try:
        # converte arquivo em wav
        subprocess.run(['ffmpeg','-y','-i', file_path, '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1', 'copy', path_media_audio])

        # converte arquivo wav em mp3
        convert = AudioSegment.from_wav(path_media_audio)
        audio_file = convert.export('exemplo.mp3', format="mp3")
        
        if audio_file:
            print("<<<<<<<<<<<< PREPARAÇAO AUDIO CONCLUIDA >>>>>>>>>>>>")
            preparar_transcricao(media_transcricao_id, audio_file)
        else:
            print("<<<<<<<<<<<< ERRO AO PREPARAR AUDIO >>>>>>>>>>>>")
            atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_PROCESSAMENTO)
    
    except Exception as e:
        print("<<<<<<<<<<<< ERRO AO PREPARAR AUDIO >>>>>>>>>>>>")
        atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_PROCESSAMENTO)


def preparar_transcricao(media_transcricao_id, audio_file):

    # envia arquivo para OpenAI
    instance = models.MediaTranscricao.objects.get(pk=media_transcricao_id)
    arquivo_file = instance.arquivo
    filename_audio = str(arquivo_file.name).split('.')[-2].split('/')[1]
    path_media_legenda = f'{ROOT_LEGENDA}/{filename_audio}.vtt'
    
    print("<<<<<<<<<<<< PREPARANDO TRANSCRIÇÃO >>>>>>>>>>>>")
    atualizar_status_transcricao(media_transcricao_id, STATUS_FAZENDO_TRANSCRICAO)

    try: 
        client = OpenAI(api_key="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")
        transcricao = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="verbose_json"
        )

        if transcricao:
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
                        'tempo_inicial': convert_to_time(t.get('start'), False),
                        'tempo_final': convert_to_time(t.get('end'), False),
                        'tempo_inicial_segundos': int(t.get('start'))
                    }
                    transcricao = models.Transcricao(**dict_transcricao)
                    transcricao.save()
                
                instance.legenda = f'legenda_transcricao/{filename_audio}.vtt'
                instance.save()
                    
            vtt.close()
            print("<<<<<<<<<<<< TRANSCRIÇÃO CONCLUIDA >>>>>>>>>>>>")
            atualizar_status_transcricao(media_transcricao_id, STATUS_CONCLUIDO)
        else:
            print("<<<<<<<<<<<< FALHA NA TRANSCRIÇÃO >>>>>>>>>>>>")
            atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_TRANSCRICAO)

    except Exception as e:
        print("<<<<<<<<<<<< FALHA NA TRANSCRIÇÃO >>>>>>>>>>>>")
        atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_TRANSCRICAO)


# def criar_chat_transcricao():
#     path_media_pdf = f'{ROOT_PDF}/{filename_audio}.pdf'
        
#     pdfkit.from_string(texto_total, path_media_pdf,options={'encoding': "UTF-8",})

#     dict_chat = {
#         'titulo': filename_audio,
#         'documento': f'documento_chat/{filename_audio}.pdf',
#         'ativo': True,
#         'usuario': instance.criado_por,
#     }
    
#     chat = models.Chat(**dict_chat)
#     chat.save()
    
#     instance.chat = chat
#     instance.save()


@background(name="Processar Transcrições")
def processar_transcricoes():
    ocupado = models.MediaTranscricao.objects.filter(status__in=[STATUS_FAZENDO_TRANSCRICAO, STATUS_PROCESSANDO_ARQUIVO], ativo=True).exists()
    print('Executando ......')
    if not ocupado:
        CompletedTask.objects.all().delete()
        transcricao = models.MediaTranscricao.objects.filter(status=STATUS_FILA_PROCESSAMENTO).order_by('id').first()
        if transcricao:
            print('Processando...')
            preparar_audio(transcricao.id)
