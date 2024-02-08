from apps.contrib.helpers import base_url, qrcode
from .models import Certidao


def url_img_mobile(user):
    certidao = Certidao.objects.filter(criado_por=user,assinatura = False).first()
    if not certidao:
        certidao = Certidao.objects.create()
        
    url = '{0}?certidao={1}'.format(base_url('certidao_localizacao/assinar-certidao'),certidao.get_encrypt_id())
    return {
        'img':qrcode(url, '300x300'),
        'certidao_id': certidao.id
    }