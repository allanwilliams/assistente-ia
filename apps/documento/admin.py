from django.contrib import admin
from apps.core.mixins import AuditoriaAdmin
from apps.documento.models import Mensagem, Chat, MediaTranscricao, Transcricao

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

    list_display = ('titulo',  'ativo', 'arquivo','legenda')


@admin.register(Transcricao)
class TranscricaoAdmin(AuditoriaAdmin):
    search_fields = (
        'texto',
    )

    list_display = ('media_transcricao', 'texto')

