from django.urls import path, include
from .views import chat,dashboard, transcricao_video, transcricao, export_chat_txt

app_name = "documento"
urlpatterns = [
    path("api/", include("apps.documento.api.urls")),
    path('chat/', chat, name='chat'),
    path('export-chat-txt/<id>', export_chat_txt, name='export_chat_txt'),
    path('transcricao/', transcricao, name='transcricao'),
    path('dashboard/', dashboard, name='dashboard'),
    path('transcricao-video/', transcricao_video, name='transcricao_video')
]
