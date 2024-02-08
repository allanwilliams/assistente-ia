from django.urls import path, include
from apps.core.views import dash,dash_blog
app_name = "core"
urlpatterns = [
    path("api/", include("apps.core.api.urls")),
    path("dash-blog/", view=dash_blog, name="dashboard_blog"),
]
