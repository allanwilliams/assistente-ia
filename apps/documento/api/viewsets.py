from rest_framework.viewsets import ModelViewSet
from apps.documento.models import Chat, Mensagem
from apps.documento.api.serializers import ChatSerializer, MensagemSerializer
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


class MensagemFilter(filters.FilterSet):
    class Meta:
        model = Mensagem
        fields = {
            'criado_por': ['exact'],
            'is_favorito': ['exact'],
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
        # nova_msg = Mensagem(chat_id=chat, texto=texto, autor=autor)
        # nova_msg.save()

        # chatpdf_source_id = nova_msg.chat.chatpdf_source_id

        # headers = {
        #     'x-api-key': 'sec_16KMXQwy0VcwkGz7xYuDY9PxWGGgsHM6',
        #     "Content-Type": "application/json",
        # }

        # data = {
        #     "referenceSources": True,
        #     'sourceId': chatpdf_source_id,
        #     'messages': [
        #         {
        #             'role': "user",
        #             'content': texto,
        #         }
        #     ]
        # }

        # response = requests.post(
        #     'https://api.chatpdf.com/v1/chats/message', headers=headers, json=data)

        # resposta_chatpdf = Mensagem(chat_id=chat, texto='', autor=CHAT_AUTOR_IA)
        
        # if response.status_code == 200:
        #     resposta_chatpdf.texto = response.json()['content']
        # else:
        #     resposta_chatpdf.texto = 'Erro ao responder'

        # resposta_chatpdf.save()
        return Response({ "texto": CQ.texto, "autor": CQ.autor }, status=status.HTTP_201_CREATED)
