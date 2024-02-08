from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from apps.contrib.models import AssinaturaDocumento

@require_http_methods(["GET","POST"])
def verificar_assinatura(request):
    if request.method == 'GET':
        token_url = request.GET.get('token')
        if token_url:
            template = 'validar_assinatura_qrcode.html'
            assinatura = AssinaturaDocumento.objects.filter(token=token_url).first()

            doc_valido = True if assinatura else False

            context = {
                'doc_valido': doc_valido,
            }

            if doc_valido:
                context['assinatura'] = assinatura

            return render(request, template, context)

    if request.method == 'POST':
        token_input = request.POST.get('token')
        assinatura = AssinaturaDocumento.objects.filter(token=token_input).first()
        template = 'validar_assinatura.html'
        
        doc_valido = True if assinatura else False
        
        if doc_valido:
            context = {
                'doc_valido': doc_valido,
            }
            
            context['assinatura'] = assinatura
        else:
            context = {
                'doc_invalido': True,
            }

        return render(request, template, context)

    return render(request, 'validar_assinatura.html')