from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import Group
from apps.users.models import Papeis
from apps.django_sso_app.helpers import get_user
from apps.core.utils import core_decrypt
import re

class MyAuthenticationBackend(OIDCAuthenticationBackend):  # pragma: no cover
    # Filtra as roles baseadas no tipo
    def get_roles(self,roles,tipo):
        new_roles = []
        padrao = r'\[(.*?)\]'
        for role in roles:
            if tipo in role:
                resultado = re.search(padrao, role)

                if resultado:
                    elemento = resultado.group(1)
                    new_roles.append(elemento)

        return new_roles
    
    # Usa as roles IS_ADMIN e IS_STAFF para habilitar as flags do usuário
    def handle_flags(self,user,roles):
        if roles:
            user.is_superuser = 'FLAG[IS_ADMIN]' in roles
            user.is_staff = 'FLAG[IS_STAFF]' in roles

    # Usa as roles de grupos para determinar os grupos do usuário
    def handle_groups(self,user,roles):
        roles = self.get_roles(roles,'GRUPO')
        
        if roles:
            for ugp in user.groups.all():
                if ugp.name not in roles:
                    user.groups.remove(ugp)
            for groupr in roles:
                group = Group.objects.filter(name=groupr).first()
                if group:
                    user.groups.add(group)
        else:
            for ugp in user.groups.all():
                user.groups.remove(ugp)

    # Usa as roles de papel para determinar os grupos do usuário
    def handle_papeis(self,user,roles):
        roles = self.get_roles(roles,'PAPEL')
        if roles:
            for papel in roles:
                papel_obj = Papeis.objects.filter(titulo=papel).first()
                if papel_obj:
                    user.papel = papel_obj

    # configura o usuário com base nas roles recebidas
    def manager_user(self,user, claims):
        sub = claims.get('sub','')
        if sub:
            self.populate_additional_userdata(sub,user)
            user.fusionauth_user_id = sub
            
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.name = claims.get('name', '')
        preferred_username = claims.get('preferred_username', '')
        if preferred_username:
            user.username = preferred_username

        roles = claims.get('roles', '')
        if roles:
            self.handle_flags(user,roles)
            self.handle_groups(user,roles)
            self.handle_papeis(user,roles)
    
    def populate_additional_userdata(self,sub,user):
        fusion_user = get_user(sub)
        if fusion_user:
            userdata = fusion_user['user']['data']
            if userdata:
                for data in userdata:
                    if hasattr(user,data):
                        dado = core_decrypt(userdata[data])
                        setattr(user,data,dado)
                user.save()

    def create_user(self, claims):
        user = super(MyAuthenticationBackend, self).create_user(claims)
        self.manager_user(user,claims)
        user.save()
        return user

    def update_user(self, user, claims):
        self.manager_user(user,claims)
        user.save()
        return user
    

