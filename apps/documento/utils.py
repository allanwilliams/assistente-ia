

import requests
import subprocess
import json
from pydub import AudioSegment
from datetime import timedelta
from openai import OpenAI
import pdfkit
from config.settings import ROOT_DIR
from apps.documento import models
from background_task import background
from background_task.models import CompletedTask
import subprocess
from scipy.io import wavfile
import noisereduce as nr
import torch
from pyannote.audio import Pipeline
import os
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

from apps.documento.choices import (
    CHAT_AUTOR_IA, 
    STATUS_PROCESSANDO_ARQUIVO,
    STATUS_FALHA_PROCESSAMENTO,
    STATUS_FAZENDO_TRANSCRICAO,
    STATUS_FALHA_TRANSCRICAO,
    STATUS_CONCLUIDO,
    STATUS_FILA_PROCESSAMENTO
)


ROOT_MEDIA = f'{ROOT_DIR}/media'
ROOT_LEGENDA = f'{ROOT_DIR}/media/legenda_transcricao'
ROOT_PDF = f'{ROOT_DIR}/media/documento_chat'

DEEPGRAM_API_KEY = "29f98c5edc5065f3f8d644149ba08b38eb942e5c"

def create_questions(*args, **kwargs):
    from .models import Chat, Mensagem 
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

def convert_mp3_to_wav(mp3_path, wav_path):
    # Comando ffmpeg para converter MP3 para WAV com taxa de amostragem de 16kHz
    # command = ['ffmpeg','-y','-i', mp3_path, '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 'copy', wav_path]
    command = ['ffmpeg','-y', '-i', mp3_path, '-ar', '16000', '-ac', '1', wav_path]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def process_audio(audio_path):
    convert_mp3_to_wav(audio_path,'converted_mp3.wav')
    rate, data = wavfile.read("converted_mp3.wav")
    # perform noise reduction
    reduced_noise = nr.reduce_noise(y=data, sr=rate)
    wavfile.write("audio_temporario.wav", rate, reduced_noise)

    return "audio_temporario.wav"

def get_diarizations(audio):
    print("<<<<<<<<<<<< PREPARANDO DIARIZAÇAO >>>>>>>>>>>>")
    try:
        pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token="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")

        pipeline.to(torch.device("cpu"))

        # apply pretrained pipeline
        diarization = pipeline(audio,num_speakers=2,max_speakers=3)

        # print the result
        result = [{
            'start': f'{turn.start:.1f}',
            'stop': f'{turn.end:.1f}',
            'speaker': speaker
        } for turn, _, speaker in diarization.itertracks(yield_label=True)]
        print("<<<<<<<<<<<< DIARIZACAO CONCLUIDA >>>>>>>>>>>>")
        return unify_speakers(result)
    except Exception as e:
        print("<<<<<<<<<<<< ERRO DIARIZACAO >>>>>>>>>>>>", e)

def get_speaker(diarization,start_interval,stop_interval):
    filtered_elements = [element for element in diarization if float(start_interval) >= float(element['start']) and float(stop_interval) <= float(element['stop'])]
    return filtered_elements[0]['speaker'] if filtered_elements else 'Não identificado'

def unify_speakers(data):
    print("<<<<<<<<<<<< UNIFY SPEAKERS >>>>>>>>>>>>")
    try:
        unified = []
        current_speaker = None
        current_start = None
        current_stop = None

        for item in data:
            start = float(item['start'])
            stop = float(item['stop'])
            speaker = item['speaker']

            # Se é o mesmo speaker e o intervalo é contínuo ou se sobrepõe, atualize o 'stop'
            if speaker == current_speaker:
                current_stop = max(current_stop, stop)
            else:
                if current_speaker is not None:
                    unified.append({'start': str(current_start), 'stop': str(current_stop), 'speaker': current_speaker})
                
                current_speaker = speaker
                current_start = start
                current_stop = stop

        # Não esqueça de adicionar o último intervalo após sair do loop
        if current_speaker is not None:
            unified.append({'start': str(current_start), 'stop': str(current_stop), 'speaker': current_speaker})

        return unified
    except Exception as e:
         print("<<<<<<<<<<<< UNIFY SPEAKERS ERROR>>>>>>>>>>>>", e)

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
    try:
        instance = models.MediaTranscricao.objects.get(pk=media_transcricao_id)
        filename_audio = str(instance.arquivo.name).split('/')[1].split('.')[-2]
        path_media_audio = f'{ROOT_MEDIA}/{filename_audio}.wav'

        file_path = '{}/{}'.format(ROOT_MEDIA, instance.arquivo)
        
        print("<<<<<<<<<<<< PREPARANDO AUDIO >>>>>>>>>>>>")
        atualizar_status_transcricao(media_transcricao_id, STATUS_PROCESSANDO_ARQUIVO)

        # converte arquivo em wav
        subprocess.run(['ffmpeg','-y','-i', file_path, '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1', 'copy', path_media_audio])

        # converte arquivo wav em mp3
        convert = AudioSegment.from_wav(path_media_audio)
        audio_file = convert.export('temp_audio_file.mp3', format="mp3")
        
        os.remove(path_media_audio)

        if audio_file:
            print("<<<<<<<<<<<< PREPARAÇAO AUDIO CONCLUIDA >>>>>>>>>>>>")
            # preparar_transcricao(media_transcricao_id, audio_file)
            preparar_transcricao_deepgram(media_transcricao_id, audio_file)
        else:
            print("<<<<<<<<<<<< ERRO AO PREPARAR AUDIO >>>>>>>>>>>>")
            atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_PROCESSAMENTO)
    
    except Exception as e:
        print("<<<<<<<<<<<< ERRO AO PREPARAR AUDIO >>>>>>>>>>>>", e)
        atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_PROCESSAMENTO)


def preparar_transcricao(media_transcricao_id, audio_file):
    try: 
        # envia arquivo para OpenAI
        instance = models.MediaTranscricao.objects.get(pk=media_transcricao_id)
        arquivo_file = instance.arquivo
        filename_audio = str(arquivo_file.name).split('/')[1].split('.')[-2]
        path_media_legenda = f'{ROOT_LEGENDA}/{filename_audio}.vtt'
        
        print("<<<<<<<<<<<< PREPARANDO TRANSCRIÇÃO >>>>>>>>>>>>")
        atualizar_status_transcricao(media_transcricao_id, STATUS_FAZENDO_TRANSCRICAO)

        client = OpenAI(api_key="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")
        transcricao = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="verbose_json"
        )

        if transcricao:
            print('audio_file.name', audio_file.name)
            # diarization = get_diarizations(audio_file.name)
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
                        'tempo_inicial_segundos': int(t.get('start')),
                        # 'speaker': get_speaker(diarization,t.get('start'),t.get('end'))
                        'speaker': 'Não identificado'
                    }
                    transcricao_new = models.Transcricao(**dict_transcricao)
                    transcricao_new.save()
                
                instance.legenda = f'legenda_transcricao/{filename_audio}.vtt'
                # instance.diarizacao = diarization
                transcricao_obj = {
                    "segments": transcricao.segments,
                }
                instance.transcricao = json.dumps(transcricao_obj)
                instance.save()
                    
            vtt.close()
            print("<<<<<<<<<<<< TRANSCRIÇÃO CONCLUIDA >>>>>>>>>>>>")
            atualizar_status_transcricao(media_transcricao_id, STATUS_CONCLUIDO)
        else:
            print("<<<<<<<<<<<< FALHA NA TRANSCRIÇÃO >>>>>>>>>>>>")
            atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_TRANSCRICAO)

    except Exception as e:
        print("<<<<<<<<<<<< FALHA NA TRANSCRIÇÃO EXCEPT >>>>>>>>>>>>", e)
        atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_TRANSCRICAO)


def preparar_transcricao_deepgram(media_transcricao_id, audio_file):
    try: 
        instance = models.MediaTranscricao.objects.get(pk=media_transcricao_id)
        arquivo_file = instance.arquivo
        filename_audio = str(arquivo_file.name).split('/')[1].split('.')[-2]
        path_media_legenda = f'{ROOT_LEGENDA}/{filename_audio}.vtt'
        
        print("<<<<<<<<<<<< PREPARANDO TRANSCRIÇÃO >>>>>>>>>>>>")
        atualizar_status_transcricao(media_transcricao_id, STATUS_FAZENDO_TRANSCRICAO)

        deepgram = DeepgramClient(DEEPGRAM_API_KEY)

        payload: FileSource = {
            "buffer": audio_file,
        }

        options = PrerecordedOptions(
            # model="nova-2",
            model="whisper-large",
            # model="whisper-medium",
            language="pt-BR",
            smart_format=True, 
            punctuate=True, 
            paragraphs=True, 
            diarize=True, 
        )

        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options, timeout = 900)

        paragrafos = response.results.channels[0].alternatives[0].paragraphs.paragraphs

        if paragrafos:
            texto_total = ""
            cores_avatar = ['#0000FF', '#000000', '#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#00FFFF', '#8B00FF']
            with open(path_media_legenda, 'w') as vtt:
                vtt.write('WEBVTT\n')

                for p in paragrafos:
                    
                    for s in p.sentences:
                        start = convert_to_time(s.start, True)
                        end = convert_to_time(s.end, True)
                        text = s.text

                        vtt.write(f'{start} --> {end}\r')
                        vtt.write(f'{str(text).strip()}\r')

                        texto_total += f'{start} - {end}</br>'
                        texto_total += f'{text}</br>'

                        dict_transcricao = {
                            'media_transcricao': instance,
                            'texto': text,
                            'tempo_inicial': convert_to_time(s.start, False),
                            'tempo_final': convert_to_time(s.end, False),
                            'tempo_inicial_segundos': int(s.start),
                            'speaker': f"Orador {p.speaker}",
                            'cor_speaker': cores_avatar[p.speaker]
                        }
                        transcricao_new = models.Transcricao(**dict_transcricao)
                        transcricao_new.save()


                instance.legenda = f'legenda_transcricao/{filename_audio}.vtt'
                instance.save()
                    
            vtt.close()

            print("<<<<<<<<<<<< TRANSCRIÇÃO CONCLUIDA >>>>>>>>>>>>")
            atualizar_status_transcricao(media_transcricao_id, STATUS_CONCLUIDO)
        else:
            print("<<<<<<<<<<<< FALHA NA TRANSCRIÇÃO >>>>>>>>>>>>")
            atualizar_status_transcricao(media_transcricao_id, STATUS_FALHA_TRANSCRICAO)
    except Exception as e:
        print("<<<<<<<<<<<< FALHA NA TRANSCRIÇÃO EXCEPT >>>>>>>>>>>>", e)
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
