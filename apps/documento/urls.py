from django.urls import path, include
from .views import chat,dashboard, transcricao_video

app_name = "documento"
urlpatterns = [
    path("api/", include("apps.documento.api.urls")),
    path('chat/', chat, name='chat'),
    path('dashboard/', dashboard, name='dashboard'),
    path('transcricao-video/', transcricao_video, name='transcricao_video')
]
