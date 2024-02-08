from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import check_password
from django.conf import settings
from apps.users.models import TrocaSenhaUsuario
import string
import re

class UpperCase:
    def __init__(self, min_length=1):
        self.min_length = min_length
        
    def validate(self, password, user=None):
        if settings.USE_FUSIONAUTH: # pragma: no cover
            return
        
        invalid = True
        count = 0
        for caractere in password:
            if caractere.isupper():
                count += 1
                
        if count >= self.min_length:
            invalid = False
            
        if invalid:
            raise ValidationError(
                _("Esta senha precisa conter pelo menos %(min_length)d caractere(s) maiúsculo(s)."),
                code="password_uppercase",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        return _(
            "Sua senha precisa conter pelo menos %(min_length)d caractere(s) maiúsculo(s)."
            % {"min_length": self.min_length}
        )
        
class SpecialCase:
    def __init__(self, min_length=1):
        self.min_length = min_length
        
    def validate(self, password, user=None):
        if settings.USE_FUSIONAUTH: # pragma: no cover
            return
        
        invalid = True
        caracteres_especiais = set(string.punctuation)
        count = 0
        for caractere in password:
            if caractere in caracteres_especiais:
                count += 1
                
        if count >= self.min_length:
            invalid = False
            
        if invalid:
            raise ValidationError(
                _("Esta senha precisa conter pelo menos %(min_length)d  caractere(s) especial."),
                code="password_special",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        return _(
            "Sua senha precisa conter pelo menos %(min_length)d caractere(s) especial."
            % {"min_length": self.min_length}
        )
        
class RepeticaoCase:
    def __init__(self, min_length=1):
        self.min_length = min_length
        
    def validate(self, password, user=None):
        if settings.USE_FUSIONAUTH: # pragma: no cover
            return
        
        tamanho = len(password)
        quantidade_repeticoes = self.min_length
        invalid = True
        for i in range(quantidade_repeticoes, tamanho):
            for j in range(quantidade_repeticoes):
                if password[i - j] != password[i]:
                    break
            
            invalid =  False
                
        if invalid:
            raise ValidationError(
                _("Esta senha não pode ter mais de %(min_length)d  caracteres repetidos."),
                code="password_repeat",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        return _(
            "Sua senha não pode ter mais de %(min_length)d  caracteres repetidos."
            % {"min_length": self.min_length}
        )
        
class AcentoCase:
    def validate(self, password, user=None):
        if settings.USE_FUSIONAUTH: # pragma: no cover
            return
        
        padrao = re.compile(r'[á-â-ã-é-ê-í-ï-ó-ô-õ-ö-ú-ç-ñ-Á-Â-Ã-É-Í-Ï-Ó-Ô-Õ-Ö-Ú]+')
        invalid = bool(padrao.search(password))
        
        if invalid:        
            raise ValidationError(
                _("Esta senha não pode possuir acentos."),
                code="password_special",
            )

    def get_help_text(self):
        return "Sua senha não pode possuir acentos."

class OldPassword:
    def __init__(self, min_length=1):
        self.min_length = min_length
        
    def validate(self, password, user=None):
        if settings.USE_FUSIONAUTH: # pragma: no cover
            return
        
        if not user:
            return
        invalid = False
            
        if user:
            senhas_antigas = TrocaSenhaUsuario.objects.filter(user=user).order_by('-id')[:self.min_length]
            for pw in senhas_antigas:
                invalid = check_password(password,pw.password)
                if invalid: break
        
        if invalid:
            raise ValidationError(
                "Sua senha não pode ser igual a(s) última(s) %(min_length)d utilizada(s)",
                code="password_old",
                params={"min_length": self.min_length}
            )

    def get_help_text(self):
        return _(
            "Sua senha não pode ser igual a(s) última(s) %(min_length)d utilizada(s)"
            % {"min_length": self.min_length}
        )