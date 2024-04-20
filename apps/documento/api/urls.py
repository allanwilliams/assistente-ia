from rest_framework.routers import DefaultRouter
from apps.documento.api.viewsets import (
    ChatViewSet, 
    MensagemViewSet, 
    MediaTranscricaoViewSet, 
    TranscricaoViewSet, 
    AssistenteTopicoViewSet, 
    AssistenteMensagemViewSet,
    AssistentePerfilViewSet
)

router = DefaultRouter()
router.register(r'chat', ChatViewSet , basename='chat')
router.register(r'mensagem', MensagemViewSet , basename='mensagem')
router.register(r'media-transcricao', MediaTranscricaoViewSet , basename='media_transcricao')
router.register(r'transcricao', TranscricaoViewSet , basename='transcricao')
router.register(r'assistente-topico', AssistenteTopicoViewSet, basename='assistente_topico')
router.register(r'assistente-mensagem', AssistenteMensagemViewSet , basename='assistente_mensagem')
router.register(r'assistente-perfil', AssistentePerfilViewSet , basename='assistente_perfil')
urlpatterns = router.urls
