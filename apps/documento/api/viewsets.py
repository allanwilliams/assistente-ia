from rest_framework.viewsets import ModelViewSet
from apps.documento.models import Chat, Mensagem, MediaTranscricao, Transcricao
from apps.documento.api.serializers import ChatSerializer, MensagemSerializer, MediaTranscricaoSerializer, TranscricaoSerializer
import requests
from rest_framework.response import Response
from rest_framework import status
import json
from django_filters import rest_framework as filters
from apps.documento.choices import CHAT_AUTOR_IA
from ..utils import create_questions

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


class MensagemViewSet(ModelViewSet):
    queryset = Mensagem.objects.all()
    serializer_class = MensagemSerializer
    filterset_class = MensagemFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']


    def create(self, request, *args, **kwargs):

        chat = request.POST.get('chat')
        texto = request.POST.get('texto')
        autor = request.POST.get('autor')

        CQ = create_questions(chat=chat,texto=texto,autor=autor)
        
        return Response({"id": CQ.id, "texto": CQ.texto, "autor": CQ.autor }, status=status.HTTP_201_CREATED)

class MediaTranscricaoViewSet(ModelViewSet):
    queryset = MediaTranscricao.objects.all()
    serializer_class = MediaTranscricaoSerializer
    filterset_class = MediaTranscricaoFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']

class TranscricaoViewSet(ModelViewSet):
    queryset = Transcricao.objects.all()
    serializer_class = TranscricaoSerializer
    http_method_names = ['get', 'patch', 'post', 'delete','put']

    