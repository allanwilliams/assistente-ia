from rest_framework.routers import DefaultRouter
from django.urls import include, path

router = DefaultRouter()
urlpatterns = router.urls
urlpatterns += [
    path('general/', include('apps.core.api.urls_general')),
]
