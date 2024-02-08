from rest_framework.viewsets import ModelViewSet
from django_filters import rest_framework as filters

from apps.lembrete.models import Lembretes
from .serializers import LembretesSerializer
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
class ResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 50


class LembretesFilter(filters.FilterSet):
    class Meta:
        model = Lembretes
        fields = {
            'destinatario__id': ['exact'],
            'criado_por__id': ['exact'],
            'lembrete_proprio': ['exact'],
            'status': ['in'],
        }

class LembretesViewSet(ModelViewSet):
    queryset = Lembretes.objects.order_by('-criado_em').all()
    serializer_class = LembretesSerializer
    filterset_class = LembretesFilter
    pagination_class = ResultsSetPagination
    http_method_names = ['get', 'put', 'patch', 'post', 'head', 'delete']
    permission_classes = [IsAdminUser,]