from django.contrib.auth import  login
from apps.users.models import User
from django.shortcuts import redirect
import base64
from apps.django_sso_app.helpers import search_user
from apps.django_sso_app.MyAuthenticationBackend import MyAuthenticationBackend
from django.conf import settings

class AutoLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        email = request.GET.get('t-ns')
        is_dialog = request.GET.get('is-d')
        response = self.get_response(request)
            
        if email and is_dialog and settings.USE_FUSIONAUTH:
            email = base64.b64decode(email).decode("utf-8")
            user = search_user(email)
            if user:
                claims = self.get_user_claims(user)
                user_login = User.objects.filter(email=email).first()
                if not user_login:
                    dict_user = {
                        'email':email,
                        'first_name': user['user']['firstName'],
                        'last_name': user['user']['lastName'],
                        'fusionauth_user_id': user['user']['id'],
                        'name': user['user']['fullName'],
                    }
                    user_login = User(**dict_user)
                    user_login.save()
                roles = claims.get('roles', '')

                MyAuthenticationBackend.handle_flags(MyAuthenticationBackend,user_login,roles)
                user_login.save()
                user_login = User.objects.filter(email=email).first()
                if user_login and not request.user.is_authenticated or user_login != request.user:
                    login(request,user_login,backend='apps.django_sso_app.MyAuthenticationBackend.MyAuthenticationBackend')
                return redirect(request.META['PATH_INFO'].split('/?t-ns')[0])
        
        return response
    
    def get_user_application_roles(self,user):
        registration = user['user']['registrations']
        for r in registration:
            if r['applicationId'] == settings.OIDC_RP_CLIENT_ID:
                return r['roles']

        return []
    
    def get_user_claims(self,user):
        return {
            'applicationId': settings.OIDC_RP_CLIENT_ID,
            'email': user['user']['email'],
            'email_verified': True,
            'family_name': user['user']['lastName'],
            'given_name': user['user']['firstName'],
            'middle_name': user['user']['middleName'],
            'name': user['user']['fullName'],
            'roles': self.get_user_application_roles(user),
            'scope': 'openid email',
            'sub': user['user']['id'],
            'tid': user['user']['tenantId']
        }

   