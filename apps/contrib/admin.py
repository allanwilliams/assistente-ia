from django.contrib import admin
from apps.contrib.models import Estados
from apps.core.mixins import AuditoriaAdmin

@admin.register(Estados)
class EstadosAdmin(AuditoriaAdmin):
    search_fields = (
        'nome',
        'sigla',
    )
    list_filter = ()
    list_display = ('nome', )