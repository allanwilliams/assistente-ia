from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
from apps.contrib.helpers import get_hash, url_img_token, url_verificador
from apps.contrib.models import Estados, AssinaturaDocumento
from apps.core.encrypt_url_utils import decrypt
from apps.certidao_localizacao.models import Certidao
from geopy.geocoders import Nominatim

@require_http_methods(["GET"])
def render_pdf(request): # pragma: no cover
    from wkhtmltopdf.views import PDFTemplateResponse
    if request.GET.get('pk'):
        id_certidao = request.GET.get('pk')
        id_certidao = decrypt(id_certidao)
        certidao = Certidao.objects.filter(id=id_certidao).first()

        if certidao.assinatura:
            context = {
                'ip': certidao.ip,
                'municipio': certidao.municipio,
                'usuario': certidao.criado_por.name if certidao.criado_por else '',
                'matricula': certidao.criado_por.matricula,
                'data_hora': certidao.data_hora,
                'assinatura': certidao.assinatura,
                'certidao': certidao,
                'url_img_token': url_img_token(certidao.assinatura.token),
                'url_verificador': url_verificador()
            }
            
            return PDFTemplateResponse(
                request=request,
                template='certidao_localizacao.html',
                footer_template='certidao_footer.html',
                filename='certidao_localizacao.pdf',
                context=context,
                show_content_in_browser=True,
                cmd_options={
                    'margin-top': 7,
                    'enable-local-file-access': True,
                    'margin-bottom': 10,
                    'margin-right': 7,
                    'margin-left': 7,
                    'dpi': 150,
                    'viewport-size': '513 x 513',
                    'javascript-delay': 1000,
                    'no-stop-slow-scripts': True,
                })
    
    
@require_http_methods(["POST"])
def assinar_salvar(request):
    senha = request.POST.get('usuario_senha')
    certidao_enc = request.POST.get('certidao')
    certidao_id = decrypt(certidao_enc)
    lat = request.POST.get('lat')
    long = request.POST.get('long')
    
    if not lat or not long:
        messages.add_message(request, messages.ERROR,('Localização não detectada. Por favor autorize o acesso a localização do seu dispositivo!'))
        return HttpResponseRedirect(f"/certidao_localizacao/assinar-certidao?certidao={certidao_enc}")
    
    certidao = Certidao.objects.get(pk=certidao_id)
    usuario_logado = certidao.criado_por
    if settings.USE_FUSIONAUTH: # pragma: no cover
        autenticado = usuario_logado.test_fusionauth_password(senha)
    else:
        autenticado = usuario_logado.check_password(senha)

    if autenticado:
        token_validador = get_hash()
        data_hora = datetime.now()
        dic_assinatura = {
            'token': token_validador,
            'criado_em': data_hora,
            'criado_por': usuario_logado
        }
        assinatura = AssinaturaDocumento(**dic_assinatura)
        assinatura.save()

        geolocator = Nominatim(user_agent="defensoria_publica_estado_ceara")
        location = geolocator.reverse(f"{lat}, {long}")
        address = location.raw['address']
        estado_nome = address.get('state','Ceará')
        estado = Estados.objects.filter(nome=estado_nome).first()
        ip = request.META.get('HTTP_X_REAL_IP')
        certidao.ip = ip
        certidao.estado = estado
        certidao.latitude = lat
        certidao.longitude = long
        certidao.data_hora = data_hora
        municipio = address.get('city','')  
        if municipio == '':
            municipio = address.get('town','')  
        certidao.municipio = municipio
        certidao.assinatura = assinatura
        certidao.save()

        return render(request,'assinatura_mobile.html',context={'sucesso':True, 'certidao_id': certidao_enc})
    else:
        messages.add_message(request, messages.ERROR,('Senha incorreta!'))
        return HttpResponseRedirect(f"/certidao_localizacao/assinar-certidao?certidao={certidao_enc}")

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

@require_http_methods(["GET"])
def assinar_certidao(request):
    certidao_id = request.GET.get('certidao')
    certidao_id = decrypt(certidao_id)

    certidao = Certidao.objects.get(pk=certidao_id)
    if certidao.assinatura:
        return render(request,'assinatura_mobile.html', context={'assinado':True})
    else:
        return render(request,'assinatura_mobile.html')
    