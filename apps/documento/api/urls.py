from rest_framework.routers import DefaultRouter
from apps.documento.api.viewsets import (
    ChatViewSet, MensagemViewSet
)

router = DefaultRouter()
router.register(r'chat', ChatViewSet , basename='chat')
router.register(r'mensagem', MensagemViewSet , basename='mensagem')
urlpatterns = router.urls
