from .models import LogRequests, UserPage
import json
from .models import UserSession
from threading import Thread
from asgiref.sync import sync_to_async
import asyncio
import datetime
from django.db.utils import InterfaceError
from django.utils import timezone
from django.shortcuts import redirect
from apps.users.models import UserPreferencias

admin_url = '/admin/'
block_list = [
    '/core/api/general/',
    '/lembrete/api/lembretes/',
    '/admin/jsi18n/',
    '/favicon.ico',
    '/resources/',
    '/app-assistido/api/user',
    '/admin/jsi',
    '/ajax_select/ajax_lookup',
    '/atendimento/api/',
    '/api/',
    '/__debug__/history_sidebar/'
]
class SessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            req = request
            if not req.user.is_authenticated and admin_url in request.META['PATH_INFO'] and '/admin/login' not in request.META['PATH_INFO']:
                return redirect('/admin/login')
            
            if self.valida_url(request.META['PATH_INFO']):
                Thread(target=self.main,args=(req,)).run()
            return self.get_response(req)
        except InterfaceError:
            asyncio.run(self.close_connection())
            return self.get_response(req)

    def valida_url(self,url):
        if '/core/api/general/session/UserPage/' in url:
            return True
        
        for bl in block_list:
            if bl in url:
                return False
        return True

    def main(self,request):
        grava_log = True
        if '/core/api/general/session/UserPage/' in request.META['PATH_INFO']:
            grava_log = False
        autenticado = asyncio.run(self.get_autenticado(request))
        params = request.POST if request.POST else request.GET

        dic_logrequest = {
            'ip': request.META['REMOTE_ADDR'],
            'ip_publico': request.META.get('HTTP_X_REAL_IP') or None,
            'navegador': request.META['HTTP_USER_AGENT'],
            'url_atual': request.META.get('HTTP_REFERER') or None,
            'url': request.META['PATH_INFO'],
            'metodo': request.method,
            'parametros': json.dumps(params,ensure_ascii=False)
        }

        if autenticado and grava_log and 'sessionid' in request.COOKIES:
            dic_logrequest.update({'session_key':request.COOKIES['sessionid']})
            dic_logrequest.update({'user':request.user})
            asyncio.run(self.get_usersession(request))
            asyncio.run(self.save_logrequests(dic_logrequest))
            asyncio.run(self.verifica_preferencia(request))
            
        staff = asyncio.run(self.is_staff(request))
        if staff:
            url = ''
            try:
                if request.META.get('HTTP_REFERER') and admin_url in request.META.get('HTTP_REFERER'):                    
                    url = admin_url + request.META.get('HTTP_REFERER').split(admin_url)[1]
                else:
                    url = request.META['PATH_INFO']
            except Exception:
                url = request.META['PATH_INFO']
                
            asyncio.run(self.save_userpage(request,url))     

    @sync_to_async
    def save_userpage(self,request,url):
        user_page = ''
        try:
            user_page, _ = UserPage.objects.get_or_create(user = request.user,url=url)
            if user_page:
                user_page.save()
        except Exception:
            try:
                UserPage.objects.filter(user = request.user,url=url).delete()
                user_page, _ = UserPage.objects.get_or_create(user = request.user,url=url)
            except Exception: pass
        if user_page:
            user_page.modificado_em = timezone.now()
            user_page.save()
                
    
    async def is_staff(self,request):
        return request.user.is_staff
    
    @sync_to_async
    def save_logrequests(self,dic_logrequest):
        try:
            session = LogRequests(**dic_logrequest)
            session.save()
        except Exception: pass

    @sync_to_async
    def get_autenticado(self,request):
        return request.user.is_authenticated

    @sync_to_async
    def get_usersession(self,request):
        try:
            user_session = UserSession.objects.filter(user = request.user.id).first()
            if user_session:
                user_session.modificado_em = timezone.now()
                user_session.save()
            return user_session

        except Exception: pass
    
    @sync_to_async
    def close_connection(self):
        from django.db import connections, connection
        connection.close()

    @sync_to_async
    def verifica_preferencia(self, request):
        if request.user:
            try:
                preferencia = UserPreferencias.objects.filter(user=request.user, preferencia=2).first()
                if preferencia and preferencia.criado_em:
                    hoje = datetime.date.today()
                    data_preferencia = preferencia.criado_em.date()
                    if hoje > data_preferencia:
                        preferencia.delete()
            except Exception:
                pass