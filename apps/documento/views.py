from django.shortcuts import render
from django.http import HttpResponse
from apps.documento.models import Chat, MediaTranscricao, Transcricao, Mensagem, AssistentePerfil
from openai import OpenAI
from pydub import AudioSegment
import subprocess
import os
from django.core.files.storage import FileSystemStorage
from config.settings import BASE_DIR
from django.utils.html import format_html
import datetime
from django.contrib.auth.decorators import login_required
from constance import config

client = OpenAI(api_key="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")

@login_required
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

@login_required
def dashboard(request):
    path = request.path 
    if 'dashboard-documento' in path:
        chats = Chat.objects.filter(criado_por=request.user, ativo=True)
        context = {
            'chats': chats,
            'api': 'chat',
            'redirect': 'chat/?documento',
            'titulo': 'Assistente de Documento Jurídico',
            'titulo_tabela': 'Meus Documentos',
            'config': config
        }

        return render(request, 'dashboard.html', context)
    
    if 'dashboard-media' in path:
        transcricoes = MediaTranscricao.objects.filter(criado_por=request.user, ativo=True)
        context = {
            'transcricoes': transcricoes,
            'api': 'media-transcricao',
            'redirect': 'transcricao/?arquivo',
            'titulo': 'Assistente de Transcrição de Media',
            'titulo_tabela': 'Minhas transcrições'
        }
        return render(request, 'dashboard.html', context)
    
    
def convert_to_time(number, microseconds=False):
    delta_tempo = datetime.timedelta(seconds=number)
    time = "{:02}:{:02}:{:02}".format(delta_tempo.seconds // 3600, (delta_tempo.seconds % 3600) // 60, delta_tempo.seconds % 60)
    if microseconds:
        microssegundos_limitados = min(delta_tempo.microseconds // 1000, 999)
        time = "{}.{:03}".format(time, microssegundos_limitados)
    return time


@login_required
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


def export_transcricoes_txt(request, id=None):
    media_transcricao = MediaTranscricao.objects.filter(id=id).first()
    favoritos = request.GET.get('favoritos')

    if media_transcricao:
        transcricoes = Transcricao.objects.filter(media_transcricao=media_transcricao)

        if favoritos:
            transcricoes = transcricoes.filter(is_favorito=True)

        texto = []
        for t in transcricoes:
            texto.append(f'{t.speaker}\n{t.tempo_inicial} --> {t.tempo_final}\n{t.texto.strip()}\n\r')

        texto = ''.join(texto) 

        response = HttpResponse(texto, content_type='text/plain;charset=UTF-8') 
        response['Content-Disposition'] = f"attachment; filename=transcricao.txt"

        return response
    


def assistente(request, id=None):

    assistente = AssistentePerfil.objects.filter(id=id).first()

    context = {
        "assistente": assistente
    }
    
    return render(request, 'assistente.html',context=context)