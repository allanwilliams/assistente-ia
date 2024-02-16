from rest_framework.viewsets import ModelViewSet
from apps.documento.models import Chat, Mensagem
from apps.documento.api.serializers import ChatSerializer, MensagemSerializer
import requests
from rest_framework.response import Response
from rest_framework import status
import json
from apps.documento.choices import CHAT_AUTOR_IA


class ChatViewSet(ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    http_method_names = ['get', 'patch', 'post', 'delete','put']

class MensagemViewSet(ModelViewSet):
    queryset = Mensagem.objects.all()
    serializer_class = MensagemSerializer
    http_method_names = ['get', 'patch', 'post', 'delete','put']


    def create(self, request, *args, **kwargs):

        chat = request.POST.get('chat')
        texto = request.POST.get('texto')
        autor = request.POST.get('autor')

        nova_msg = Mensagem(chat_id=chat, texto=texto, autor=autor)
        nova_msg.save()

        chatpdf_source_id = nova_msg.chat.chatpdf_source_id

        headers = {
            'x-api-key': 'sec_CPSnpaMaVcZyatxIozz9Jv8saovN1tbN',
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

        resposta_chatpdf = Mensagem(chat_id=chat, texto='', autor=CHAT_AUTOR_IA)
        
        if response.status_code == 200:
            resposta_chatpdf.texto = response.json()['content']
        else:
            resposta_chatpdf.texto = 'Erro ao responder'

        resposta_chatpdf.save()

        return Response({ "texto": resposta_chatpdf.texto, "autor": resposta_chatpdf.autor }, status=status.HTTP_201_CREATED)
