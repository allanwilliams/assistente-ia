from django.urls import path, include
from .views import chat

app_name = "documento"
urlpatterns = [
    path("api/", include("apps.documento.api.urls")),
    path('chat', chat, name='chat')
]
