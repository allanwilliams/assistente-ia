from rest_framework.routers import DefaultRouter
from apps.core.api.viewsets import GeneralViewSet, GetModelViewSet, GetLabelViewSet

router = DefaultRouter()
router.register(r'get-label', GetLabelViewSet, basename='get-label')
router.register(r'(?P<app_label>\w+)/get-model', GetModelViewSet, basename='get-model')
router.register(r'(?P<app_label>\w+)/(?P<model_name>\w+)(?:/(?P<id>\w+))?', GeneralViewSet, basename='general')
urlpatterns = router.urls
