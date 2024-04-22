from django.contrib import admin
from apps.core.mixins import AuditoriaAdmin
from apps.documento.models import Mensagem, Chat, MediaTranscricao, Transcricao, AssistenteMensagem, AssistenteTopico, AssistentePerfil

# Register your models here.


@admin.register(Chat)
class ChatAdmin(AuditoriaAdmin):
    search_fields = (
        'titulo',
    )

    list_display = ('titulo',  'ativo', 'documento')


@admin.register(Mensagem)
class MensagemAdmin(AuditoriaAdmin):
    search_fields = (
        'texto',
    )

    list_display = ('chat', 'autor', 'texto')

@admin.register(MediaTranscricao)
class MediaTranscricaoAdmin(AuditoriaAdmin):
    search_fields = (
        'titulo',
    )

    list_display = ('titulo',  'ativo', 'status', 'arquivo','legenda')


@admin.register(Transcricao)
class TranscricaoAdmin(AuditoriaAdmin):
    search_fields = (
        'texto',
    )
    list_filter = (
        'media_transcricao',
    )

    list_display = ('id', 'media_transcricao')


@admin.register(AssistenteMensagem)
class AssistenteMensagemAdmin(AuditoriaAdmin):
    search_fields = (
        'texto',
    )
    list_filter = (
        'topico',
    )
    list_display = ('id', 'topico', 'texto')


@admin.register(AssistenteTopico)
class AssistenteTopicoAdmin(AuditoriaAdmin):
    list_display = ('id', 'openia_thread_id')

@admin.register(AssistentePerfil)
class AssistentePerfilAdmin(AuditoriaAdmin):
    list_display = ('id', 'nome', 'openia_assistente_id')
