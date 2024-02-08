from django.urls import path

from . import views

urlpatterns = [
    path('sso-change-password', views.change_password, name='sso_change_password'),
    path('sso-login', views.login, name='sso_login'),
    path('django-sso-unauthorized', views.unauthorized, name='django_sso_unauthorized'),
]
