from django.urls import path, include

app_name = "lembrete"
urlpatterns = [
    path("api/", include("apps.lembrete.api.urls")),
]
