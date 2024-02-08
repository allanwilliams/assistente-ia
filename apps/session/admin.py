import json
from django.contrib import admin
from django.utils.html import format_html
from .models import LogRequests,UserSession
from rangefilter.filter import DateRangeFilter
from .functions import remover_sessao
from pygments.formatters import HtmlFormatter
from pygments import highlight
from pygments.lexers import JsonLexer
from django.utils.safestring import mark_safe

@admin.register(LogRequests)
class LogRequestsAdmin(admin.ModelAdmin):
    search_fields = ('user__name','url', )
    list_filter = ('user__name',('data_hora', DateRangeFilter),)
    list_display = ('user','ip_publico','url_atual','url','metodo','get_parametros','data_hora')
        
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def get_parametros(self,obj):
        try:
            parametros = json.loads(obj.parametros)
            response = json.dumps(parametros,sort_keys=True,indent=2,ensure_ascii=False)
            formatter = HtmlFormatter(style='colorful')
            response = highlight(response, JsonLexer(), formatter)
            style = "<style>pre { width: 450px; } " + formatter.get_style_defs() + "</style><br>"
            return mark_safe(style + response)
        except Exception:
            return {}
        
    get_parametros.short_description = format_html('<div class="text"><a href="">PARAMETROS</a></div>')
    
@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_filter = ('user__papel',)
    list_display = ('user','get_titulo','get_dt_login',)
    readonly_fields = ('user','session',)
    
    actions = [
        'delete_selected',
        remover_sessao
    ]
    
    def get_titulo(self,obj):
        return obj.user.papel.titulo if obj.user.papel else 'Sem papel atribuído'
    get_titulo.short_description = format_html('<div class="text"><a href="">Papel</a></div>')
    
    def get_dt_login(self,obj):
        return obj.criado_em
    get_dt_login.short_description = format_html('<div class="text"><a href="">Data login</a></div>')
    
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False