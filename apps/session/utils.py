from datetime import timedelta

from django.conf import settings
from django.utils import timezone
import humanize
from apps.users.models import TrocaSenhaUsuario


class PasswordChecker:
    """
    Checks if password has expired or if it will expire soon
    """
    def __init__(self, user):
        self.password_allowed_duration = timedelta(seconds=settings.PASSWORD_EXPIRE_SECONDS)
        self.password_warning_duration = timedelta(seconds=settings.PASSWORD_EXPIRE_WARN_SECONDS)

        self.user = user
        self.last_changed = self.get_last_changed()
        self.expiration = self.last_changed + self.password_allowed_duration
        self.warning = self.expiration - self.password_warning_duration

    def is_expired(self):
        if self.is_user_excluded():
            return False
        return timezone.now() > self.expiration

    def is_warning(self):
        if self.is_user_excluded():
            return False
        return timezone.now() > self.warning

    def get_expire_time(self):
        if self.is_warning():
            time_left = self.expiration - timezone.now()
            humanize.i18n.activate("pt_BR")
            return humanize.naturaldelta(time_left)
        else:
            return None

    def get_last_changed(self):
        try:
            ultima_troca_senha = TrocaSenhaUsuario.objects.filter(user=self.user).order_by('-id').first()
            if ultima_troca_senha and ultima_troca_senha.criado_em is not None:
                data_troca = ultima_troca_senha.criado_em
            else:
                data_troca = timezone.datetime(1969,1,1,0,0,0)
        except Exception:
            data_troca = timezone.now()
        return data_troca

    def is_user_excluded(self):
        if self.user.papel is not None and self.user.papel.id == 22:
            return False
        if not self.user.is_staff:
            return True
        if hasattr(settings, 'PASSWORD_EXPIRE_EXCLUDE_SUPERUSERS') and\
                settings.PASSWORD_EXPIRE_EXCLUDE_SUPERUSERS:
            return self.user.is_superuser
        return False
