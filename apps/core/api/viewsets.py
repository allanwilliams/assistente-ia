from rest_framework.viewsets import ModelViewSet, GenericViewSet
from .serializers import GenericAllSerializer
from rest_framework.permissions import IsAuthenticated
from django.apps import apps
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

class ResultsSetPagination(PageNumberPagination):
    page_size = 200
    page_size_query_param = 'page_size'
    max_page_size = 200


class GeneralSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = 'page_size'
    max_page_size = 1
    def get_page_size(self, request):
        if request.GET.get('paginator'):
            return 2000
        else:
            return 20

class GeneralViewSet(ModelViewSet):
    pagination_class = GeneralSetPagination
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    @property
    def model(self):
        try:
            return apps.get_model(app_label=str(self.kwargs['app_label']), model_name=str(self.kwargs['model_name']))
        except Exception:
            return None


    def valida_permissao(self,user,model,app_label,model_name):
        if not user.is_superuser:
            if model._meta.db_table in ['certidao_localizacao_certidao','session_userpage','users_defensoreslotacoes']:
                return True
            if user.has_perm(f'{app_label}.view_{model_name.lower()}'):
                return True
            return False
        return True

    def get_queryset(self):
        if self.model and self.valida_permissao(user=self.request.user,model=self.model,app_label=self.kwargs['app_label'],model_name=self.kwargs['model_name']):
            object_pk = self.kwargs.get('id')
            if object_pk:
                return self.model.objects.filter(pk=object_pk)
            if self.request.method == 'GET':
                result = self.model.objects.filter(pk__gte=0)
                for param in self.request.GET:
                    try:
                        result = result.filter(**{ param:self.request.GET.get(param) })
                    except Exception: pass
                return result.order_by('id')
        return []

    def get_serializer_class(self):
        GenericAllSerializer.Meta.model = self.model
        return GenericAllSerializer
    
class GetLabelViewSet(GenericViewSet):
    pagination_class = GeneralSetPagination
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    
    def list(self, request):
        from django.conf import settings
        local_apps = [{ 'app_label': a.split('.')[1], 'url': f"/core/api/general/{a.split('.')[1]}/get-model" } for a in settings.LOCAL_APPS] 
        return Response({'mensagem': 'Sucesso', 'results': local_apps}, status=status.HTTP_200_OK)

class GetModelViewSet(GenericViewSet):
    pagination_class = GeneralSetPagination
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    
    def list(self,request,app_label):
        app_models = [{'app_model':m.__name__, 'url': f"/core/api/general/{app_label}/{m.__name__}" } for m in apps.get_app_config(app_label).get_models()]
        return Response({'mensagem': 'Sucesso', 'results': app_models}, status=status.HTTP_200_OK)