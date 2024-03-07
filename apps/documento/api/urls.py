from rest_framework.routers import DefaultRouter
from apps.documento.api.viewsets import (
    ChatViewSet, MensagemViewSet, MediaTranscricaoViewSet, TranscricaoViewSet
)

router = DefaultRouter()
router.register(r'chat', ChatViewSet , basename='chat')
router.register(r'mensagem', MensagemViewSet , basename='mensagem')
router.register(r'media-transcricao', MediaTranscricaoViewSet , basename='media_transcricao')
router.register(r'transcricao', TranscricaoViewSet , basename='transcricao')
urlpatterns = router.urls
