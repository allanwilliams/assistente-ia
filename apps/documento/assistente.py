from openai import OpenAI, AssistantEventHandler
from typing_extensions import override
from apps.documento.choices import CHAT_AUTOR_IA
from openai.types.beta.threads import Message

OPEN_IA_API_KEY = "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"
ASSISTENTE_ID = "asst_RBsJTFh0HoUsY4ZZtqSAXUwT"

client = OpenAI(api_key=OPEN_IA_API_KEY)


class EventHandler(AssistantEventHandler):
    @override
    def on_message_done(self, message: Message):
        from .models import AssistenteMensagem, AssistenteTopico
        topico = AssistenteTopico.objects.get(openia_thread_id=message.thread_id)
        resposta_openia = AssistenteMensagem(topico_id=topico.id, texto=message.content[0].text.value, autor=CHAT_AUTOR_IA)
        resposta_openia.save()


def criar_topico():
    return client.beta.threads.create()


def criar_pergunta(*args, **kwargs):
    from .models import AssistenteMensagem, AssistenteTopico

    topico = kwargs['topico']
    texto = kwargs['texto']
    autor = kwargs['autor']

    try:
        topico = AssistenteTopico.objects.get(id=topico)

        assistente_id = topico.assistente.openia_assistente_id if topico.assistente else ASSISTENTE_ID

        assistente = client.beta.assistants.retrieve(assistente_id)
        thread = client.beta.threads.retrieve(topico.openia_thread_id)

        pergunta = AssistenteMensagem(topico=topico, texto=texto, autor=autor)
        pergunta.save()
        
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=texto,
        )

        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistente.id,
            event_handler=EventHandler(),
            ) as stream:
                stream.until_done()

        mensagem_resposta = AssistenteMensagem.objects.filter(topico=topico).last()

        return mensagem_resposta
    
    except Exception as e:
        return None    
   
