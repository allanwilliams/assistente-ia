from django.urls import path, include
from .views import chat,dashboard, transcricao, export_chat_txt, export_transcricoes_txt, assistente

app_name = "documento"
urlpatterns = [
    path("api/", include("apps.documento.api.urls")),
    path('chat/', chat, name='chat'),
    path('export-chat-txt/<id>', export_chat_txt, name='export_chat_txt'),
    path('export-transcricoes-txt/<id>', export_transcricoes_txt, name='export_transcricoes_txt'),
    path('transcricao/', transcricao, name='transcricao'),
    path('tanaka/', dashboard, name='dashboard_media'),
    path('martinha/', dashboard, name='dashboard_documento'),
    path('assistente/<id>', assistente, name='assistente'),
]
