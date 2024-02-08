from django.db import models
import django.db.models.options as options
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)
from apps.core.mixins import BaseModel
from apps.users.models import User
from django.contrib.sessions.models import Session
from django.conf import settings
from django.contrib.auth import user_logged_in, user_login_failed
import django.contrib.auth as dAuth
from django.dispatch.dispatcher import receiver
from datetime import datetime,timedelta
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone

def _update_session_auth_hash(request, user):
    """
    Updating a user's password logs out all sessions for the user.

    Take the current request and the updated user object from which the new
    session hash will be derived and update the session hash appropriately to
    prevent a password change from logging out the session from which the
    password was changed.
    """
    if hasattr(user, 'get_session_auth_hash') and request.user == user:
        request.session.cycle_key()
        request.session['_auth_user_hash'] = user.get_session_auth_hash()
        user_logged_in.send(sender=user.__class__, request=request, user=user)

dAuth.update_session_auth_hash = _update_session_auth_hash

class LogRequests(models.Model):
    DEFAULT_NAO_OBTIDO = 'Não obtido'
    cols = {
        'url': 2,
    }
    user = models.ForeignKey(
        User, 
        related_name='%(class)s_usersession',
        on_delete=models.DO_NOTHING,
        verbose_name='Usuário',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=300,blank=True,default=DEFAULT_NAO_OBTIDO)
    ip = models.CharField(max_length=20,blank=True,default=DEFAULT_NAO_OBTIDO)
    ip_publico = models.CharField(max_length=20,blank=True,default=DEFAULT_NAO_OBTIDO)
    navegador = models.CharField(max_length=300,blank=True,default=DEFAULT_NAO_OBTIDO)
    url = models.CharField(max_length=300,blank=True,default=DEFAULT_NAO_OBTIDO)
    url_atual = models.CharField(max_length=500,blank=True,default=DEFAULT_NAO_OBTIDO)
    data_hora = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    metodo  = models.CharField(max_length=10,blank=True,default=DEFAULT_NAO_OBTIDO)
    parametros  = models.TextField(blank=True,default=DEFAULT_NAO_OBTIDO)
    response = models.TextField(blank=True,default=DEFAULT_NAO_OBTIDO)
    

class UserSession(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "usuário online"
        verbose_name_plural = "Usuários online"
        
    @receiver(user_logged_in)
    def remover_sessao(sender, user, request, **kwargs):
        user.save()
        Session.objects.filter(
            usersession__user=user
        ).delete()
        request.session.save()
        UserSession.objects.get_or_create(
            user=user,
            session_id=request.session.session_key
        )
    
    def time_online(self):
        me = self.modificado_em if self.modificado_em is not None else timezone.now() - timedelta(minutes=6)
        final = timezone.now() - timedelta(minutes=5)
        
        return False if me < final  else True
    
class UserPage(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url = models.CharField('url', max_length=500)
    
    class Meta:
        verbose_name = "usuário página"
        verbose_name_plural = "Usuários página"
    

