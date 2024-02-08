from rest_framework.routers import DefaultRouter
from apps.users.api.viewsets import (
    UserPreferenciasViewSet,
    CredenciaisUsuarioViewSet
)

router = DefaultRouter()
router.register(r'user-preferencias', UserPreferenciasViewSet , basename='user_preferencias')
router.register(r'user-credenciais', CredenciaisUsuarioViewSet , basename='user_credenciais')
urlpatterns = router.urls
