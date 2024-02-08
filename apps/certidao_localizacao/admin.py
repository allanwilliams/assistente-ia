from django.contrib import admin
from .models import Certidao
from apps.core.mixins import AuditoriaAdmin
from django_currentuser.middleware import get_current_user
from .helpers import url_img_mobile
from django.utils.html import format_html


@admin.register(Certidao)
class CertidaoAdmin(AuditoriaAdmin):
    list_filter = ('municipio','assinatura','data_hora')
    list_display = ('municipio','ip','data_hora','assinatura')
       
    def get_queryset(self,request):
        queryset = super(CertidaoAdmin,self).get_queryset(request)
        current_user = get_current_user()
        queryset = queryset.filter(criado_por=current_user)
        
        return queryset
    
    def add_view(self, request, form_url='', extra_context=None):
        extra = extra_context or {}
        certidao_data = url_img_mobile(request.user)
        extra['url_img_token'] = certidao_data['img']
        extra['certidao_id'] = certidao_data['certidao_id']
            
        return super(CertidaoAdmin, self).add_view(request, form_url, extra_context=extra)
    
    add_form_template = 'certidao_mobile.html'
    
    change_form_template = 'certidao_change_form_template.html'
        
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return False
