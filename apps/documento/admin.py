from django.contrib import admin
from apps.core.mixins import AuditoriaAdmin
from apps.documento.models import Mensagem, Chat

# Register your models here.


@admin.register(Chat)
class ChatAdmin(AuditoriaAdmin):
    search_fields = (
        'titulo',
    )

    list_display = ('titulo', 'documento')


@admin.register(Mensagem)
class MensagemAdmin(AuditoriaAdmin):
    search_fields = (
        'texto',
    )

    list_display = ('chat', 'autor', 'texto')
