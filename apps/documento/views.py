from django.shortcuts import render
from django.http import HttpResponse
from apps.documento.models import Chat, MediaTranscricao, Mensagem
from openai import OpenAI
from pydub import AudioSegment
import subprocess
import os
from django.core.files.storage import FileSystemStorage
from config.settings import BASE_DIR
from django.utils.html import format_html
import datetime

client = OpenAI(api_key="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")

def chat(request):
    documento = request.GET.get('documento')
    context = {}
    if documento:
        chat = Chat.objects.filter(pk=documento).first()
        context = {
            'chat':chat
        }
        return render(request, 'chat.html',context=context)
    
    return render(request, 'chat.html',context=context)


def dashboard(request):
    chats = Chat.objects.filter(criado_por=request.user, ativo=True)
    transcricoes = MediaTranscricao.objects.filter(criado_por=request.user, ativo=True)
    context = {
        'chats': chats,
        'transcricoes': transcricoes
    }

    return render(request, 'dashboard.html', context)



def convert_to_time(number, microseconds=False):
    delta_tempo = datetime.timedelta(seconds=number)
    time = "{:02}:{:02}:{:02}".format(delta_tempo.seconds // 3600, (delta_tempo.seconds % 3600) // 60, delta_tempo.seconds % 60)
    if microseconds:
        microssegundos_limitados = min(delta_tempo.microseconds // 1000, 999)
        time = "{}.{:03}".format(time, microssegundos_limitados)
    return time


def transcricao_video(request):
    transcricoes = MediaTranscricao.objects.filter(criado_por=request.user, ativo=True)
    context = {
        'transcricoes': transcricoes
    }

    if request.method == 'POST':
        audio_file = request.FILES['audio']

        fs = FileSystemStorage()
        filename = fs.save(f'video/{audio_file.name}', audio_file)

        uploaded_file_url = fs.url(filename)
        diretorio = os.path.dirname(os.path.dirname(filename))
        diretorio_arquivo = '{}{}{}'.format(BASE_DIR,diretorio,uploaded_file_url)

        filename_audio = str(audio_file.name).split('.')[-2]

        path_media_audio = f'{BASE_DIR}/media/audio/{filename_audio}.wav'

        path_media_legenda = f'{BASE_DIR}/media/legenda/{filename_audio}.vtt'
       
        subprocess.run(['ffmpeg','-y','-i', diretorio_arquivo, '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1', 'copy', path_media_audio])

        print('video convertido em audio')
        
        convert = AudioSegment.from_wav(path_media_audio)
        audio_file = convert.export('exemplo.mp3', format="mp3")

        print('audio convertido em mp3', audio_file)

        if audio_file:
            print('enviando para openia ....')
            transcricao = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="verbose_json"
            )

            print(transcricao)

            if transcricao:
                texto_total = []
                texto_total.append('<ul>')
                
                
                with open(path_media_legenda, 'w') as vtt:
                    vtt.write('WEBVTT\n')

                    for t in transcricao.segments:
                        start = convert_to_time(t.get('start'), True)
                        end = convert_to_time(t.get('end'), True)
                        text = t.get('text')

                        vtt.write(f'{start} --> {end}\n')
                        vtt.write(f'{str(text).strip()}\n')


                        texto_total.append(f"<li><b>{convert_to_time(t.get('start'))}</b>: {text}</li>")
                vtt.close()
                texto_total.append('</ul>')
                texto_html = ''.join(texto_total)

                context['transcricao'] = format_html(texto_html)
                context['video_name'] = format_html(filename_audio)
                context['legenda_name'] = format_html(filename_audio)

    return render(request, 'transcricao_video.html', context)


def transcricao(request):
    context = {}
    arquivo = request.GET.get('arquivo')
    if arquivo:
        transcricao = MediaTranscricao.objects.get(pk=arquivo)
        context = {
            'transcricao':transcricao
        }

    return render(request, 'transcricao.html', context)
    

def export_chat_txt(request, id=None):

    chat = Chat.objects.filter(id=id).first()

    if chat:
        mensagens = Mensagem.objects.filter(chat=chat)
        texto = []
        for m in mensagens:
            persona = 'Eu' if m.autor == 1 else 'IA'
            texto.append(f'{persona}: {m.texto}\n\r')

        texto = ''.join(texto) 

        response = HttpResponse(texto, content_type='text/plain;charset=UTF-8')
        response['Content-Disposition'] = f"attachment; filename=chat.txt"

        return response