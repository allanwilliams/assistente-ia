from rest_framework.routers import DefaultRouter
from .viewsets import LembretesViewSet

router = DefaultRouter()
router.register(r'lembretes', LembretesViewSet, basename='lembretes')
urlpatterns = router.urls
