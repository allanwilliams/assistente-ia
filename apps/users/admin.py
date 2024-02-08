from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from apps.core.mixins import AuditoriaAdmin
from apps.users.models import (
    Defensores,
    User,
    DefensoresLotacoes,
    Papeis
)

from apps.users.forms import UserChangeForm, UserCreationForm

@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm

    fieldsets = (
        ("User", {
            "fields": (
                "name", 
                "papel", 
                "matricula", 
                "num_orgao_classe", 
            )
        }),
        (None, {'fields': ('username', "email", 'password')}),
        ("Informações Pessoais", {
            "fields": (
                "first_name",
                "last_name",
                "cpf", 
            )
        }),
        ("Permissões", {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    list_display = ["name", "papel", "is_superuser"]
    list_filter = ['papel']
    search_fields = ["name",]
    change_list_template = 'user_changelist_template.html'


@admin.register(Defensores)
class DefensoresAdmin(AuditoriaAdmin):
    search_fields = (
        'nome',
        'cpf',
    )

    list_display = ('nome', 'matricula', 'cpf')


@admin.register(DefensoresLotacoes)
class DefensoresLotacoesAdmin(AuditoriaAdmin):
    search_fields = (
        'defensoria',
        'defensor_nome',
        'nucleo_txt',  
    )

    list_filter = ('ativo',)
    list_display = ('defensor_nome', 'defensoria', 'data_inicio', 'data_termino', 'ativo' )
    list_display_links = ('defensor_nome', )

@admin.register(Papeis)
class PapeisAdmin(AuditoriaAdmin):
    search_fields = (
        'titulo',
    )

    list_display = ('titulo',)

