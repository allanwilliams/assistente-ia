from django.urls import path, include
from .views import assinar_salvar,verificar_assinatura,render_pdf, assinar_certidao

app_name = "certidao_localizacao"
urlpatterns = [
    path("render-pdf/", view=render_pdf, name="render-pdf"),
    path("assinar-salvar", view=assinar_salvar, name="assinar_salvar"),
    path("verificar-assinatura", view=verificar_assinatura, name="verificar_assinatura"),
    path("validar-certidao", view=verificar_assinatura, name="validar_certidao"), 
    path("assinar-certidao", view=assinar_certidao, name="assinar-certidao"), 
]