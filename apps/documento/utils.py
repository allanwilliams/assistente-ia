import requests
from .models import Chat, Mensagem 
from apps.documento.choices import CHAT_AUTOR_IA

def create_questions(*args, **kwargs):

    chat = kwargs['chat']
    texto = kwargs['texto']
    autor = kwargs['autor']
    not_save = kwargs.get('not_save')


    if not not_save:
        nova_msg = Mensagem(chat_id=chat, texto=texto, autor=autor)
        nova_msg.save()

    chatpdf_source_id = Chat.objects.get(pk=chat).chatpdf_source_id

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

    resposta_chatpdf = Mensagem(chat_id=chat, texto='', autor=CHAT_AUTOR_IA)
    
    if response.status_code == 200:
        resposta_chatpdf.texto = response.json()['content']
    else:
        resposta_chatpdf.texto = 'Erro ao responder'

    resposta_chatpdf.save()
    return resposta_chatpdf
