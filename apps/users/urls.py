from django.urls import path, include

from apps.users.views import importar_usuarios, user_perfil

app_name = "users"
urlpatterns = [
    path("api/", include("apps.users.api.urls")),
    path("importar-usuarios", view=importar_usuarios, name="importar_usuarios"),
    path("perfil/<id>", view=user_perfil, name="perfil"),
]
