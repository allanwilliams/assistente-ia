from rest_framework.viewsets import ModelViewSet
from apps.documento.models import Chat, Mensagem, MediaTranscricao, Transcricao
from apps.documento.api.serializers import ChatSerializer, MensagemSerializer, MediaTranscricaoSerializer, TranscricaoSerializer
import requests
from rest_framework.response import Response
from rest_framework import status
import json
from django_filters import rest_framework as filters
from apps.documento.choices import CHAT_AUTOR_IA, STATUS_FILA_PROCESSAMENTO, STATUS_PROCESSANDO_ARQUIVO, STATUS_FAZENDO_TRANSCRICAO
from ..utils import create_questions
from rest_framework.decorators import action
import os
from datetime import datetime, date
from constance import config

class ChatFilter(filters.FilterSet):
    class Meta:
        model = Chat
        fields = {
            'criado_por': ['exact'],
            'ativo': ['exact'],
        }

class MediaTranscricaoFilter(filters.FilterSet):
    class Meta:
        model = MediaTranscricao
        fields = {
            'criado_por': ['exact'],
            'ativo': ['exact'],
            'status': ['exact'],
        }



class MensagemFilter(filters.FilterSet):
    class Meta:
        model = Mensagem
        fields = {
            'criado_por': ['exact'],
            'is_favorito': ['exact'],
            'texto':['icontains'],
        }

class TranscricaoFilter(filters.FilterSet):
    class Meta:
        model = Transcricao
        fields = {
            'criado_por': ['exact'],
            'texto':['icontains'],
        }


class ChatViewSet(ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    filterset_class = ChatFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']

    def create(self, request, *args, **kwargs):

        hoje = date.today()
        total_video_upload_usuario = Chat.objects.filter(criado_por=request.user, criado_em__month=hoje.month, criado_em__year=hoje.year).count()

        if total_video_upload_usuario > config.DOCUMENTO_LIMITE_UPLOAD_PDF:
            mensagem = f"Você excedeu o limite máximo de {config.DOCUMENTO_LIMITE_UPLOAD_PDF} documentos analizados esse mês." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def resetar_chat(self, request, pk=None):
        chat = Chat.objects.get(id=pk)

        if chat:
            Mensagem.objects.filter(chat=chat).delete()

            headers = {'x-api-key': 'sec_Ym330Go8S2k6oDbOSAzGLOAUYuAmNQR2'}

            # Remover o chat atigo no Chat PDF
            try:
                data = {'sources': [chat.chatpdf_source_id],}
                
                response = requests.post('https://api.chatpdf.com/v1/sources/delete', json=data, headers=headers)
                response.raise_for_status()
                print('success', response)
            except Exception as e:
                return Response({'mensagem': 'Erro ao deletar o documento do ChatPDF'}, status=status.HTTP_400_BAD_REQUEST)

            # Adicionar novo pdf
            ROOT = os.path.abspath(os.path.dirname(f'media/documento_chat'))
            file_path = '{}/{}'.format(ROOT, chat.documento)

            try:
                with open(file_path, 'rb') as file:
                    files = [('file', ('file', file, 'application/octet-stream'))]
                    response = requests.post('https://api.chatpdf.com/v1/sources/add-file', headers=headers, files=files)

                    if response.status_code == 200:
                        chat.chatpdf_source_id = response.json()['sourceId']
                        chat.save()

                    else:
                        msg_inicial = 'Houve um erro ao processar o PDF'
                        nova_mensagem = Mensagem(texto=msg_inicial, chat_id=chat.id, autor=CHAT_AUTOR_IA, criado_em=datetime.now())
                        nova_mensagem.save()

            except Exception as e:
                return Response({'mensagem': 'Erro ao reenviar o documento para o ChatPDF'}, status=status.HTTP_400_BAD_REQUEST)
            

            return Response({'mensagem': 'Chat resetado'}, status=status.HTTP_200_OK)
        else:
            return Response({'mensagem': 'Chat não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class MensagemViewSet(ModelViewSet):
    queryset = Mensagem.objects.all()
    serializer_class = MensagemSerializer
    filterset_class = MensagemFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']


    def create(self, request, *args, **kwargs):
        chat = request.POST.get('chat')
        texto = request.POST.get('texto')
        autor = request.POST.get('autor')

        total_perguntas_chat = Mensagem.objects.filter(criado_por=request.user, chat_id=chat).count()

        if total_perguntas_chat > config.DOCUMENTO_LIMITE_PERGUNTAS_PDF:
            mensagem = f"Você excedeu o limite máximo de {config.DOCUMENTO_LIMITE_PERGUNTAS_PDF} perguntas para este documento." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)

        CQ = create_questions(chat=chat,texto=texto,autor=autor)
        
        return Response({"id": CQ.id, "texto": CQ.texto, "autor": CQ.autor }, status=status.HTTP_201_CREATED)

class MediaTranscricaoViewSet(ModelViewSet):
    queryset = MediaTranscricao.objects.all().order_by('-id')
    serializer_class = MediaTranscricaoSerializer
    filterset_class = MediaTranscricaoFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']

    def create(self, request, *args, **kwargs):

        hoje = date.today()
        total_video_upload_usuario = MediaTranscricao.objects.filter(criado_por=request.user, criado_em__month=hoje.month, criado_em__year=hoje.year).count()
        tem_processamento_pendente = MediaTranscricao.objects.filter(criado_por=request.user, ativo=True, status__in=[
            STATUS_FILA_PROCESSAMENTO, STATUS_PROCESSANDO_ARQUIVO, STATUS_FAZENDO_TRANSCRICAO]).exists()

        if tem_processamento_pendente:
            mensagem = f"Você tem um video em processamento no momento. Aguarde a finalização para enviar outro." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)

        if total_video_upload_usuario > config.DOCUMENTO_LIMITE_UPLOAD_VIDEO:
            mensagem = f"Você excedeu o limite máximo de {config.DOCUMENTO_LIMITE_UPLOAD_VIDEO} videos analisados esse mês." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)


        return super().create(request, *args, **kwargs)

class TranscricaoViewSet(ModelViewSet):
    queryset = Transcricao.objects.all()
    serializer_class = TranscricaoSerializer
    http_method_names = ['get', 'patch', 'post', 'delete','put']

    