from django.contrib import admin
from apps.core.mixins import AuditoriaAdmin
from apps.documento.models import Mensagem, Chat, MediaTranscricao, Transcricao, AssistenteMensagem, AssistenteTopico, AssistentePerfil

# Register your models here.


@admin.register(Chat)
class ChatAdmin(AuditoriaAdmin):
    list_filter = ('criado_por','status','ativo','criado_em','modificado_em')
    search_fields = (
        'titulo',
    )

    list_display = ('titulo',  'ativo', 'documento', 'status','criado_por','criado_em','modificado_em')


@admin.register(Mensagem)
class MensagemAdmin(AuditoriaAdmin):
    search_fields = (
        'texto',
    )

    list_display = ('chat', 'autor', 'texto')

@admin.register(MediaTranscricao)
class MediaTranscricaoAdmin(AuditoriaAdmin):
    list_filter = ('criado_por','status','ativo','criado_em','modificado_em')
    search_fields = (
        'titulo',
    )

    list_display = ('titulo',  'ativo', 'status', 'arquivo','get_duracao','get_criador','criado_em','modificado_em')

    def get_duracao(self, obj):
        if obj.duracao:
            hours = obj.duracao // 3600
            minutes = (obj.duracao % 3600) // 60
            seconds = obj.duracao % 60
            return f"{hours}h {minutes}m {seconds}s"
        return '-'

    get_duracao.short_description = 'Duração'

    def get_criador(self, obj):
        return obj.criado_por.name

    get_criador.short_description = 'Criador'
    
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
