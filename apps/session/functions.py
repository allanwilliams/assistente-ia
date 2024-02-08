from django.contrib.sessions.models import Session
from .models import UserSession

def remover_sessao(modeladmin, request, queryset):
    users_selecionados = request.get('POST').get('_selected_action')
    for user in users_selecionados:
        session = UserSession.objects.filter(user_id=user).first()
        Session.objects.filter(
            usersession__user=session.user_id
        ).delete()
remover_sessao.short_description = "Deslogar usuário"