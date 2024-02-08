import hashlib
import os
from constance import config
import requests

def get_hash():
    return hashlib.md5(os.urandom(128)).hexdigest().upper()[:16]

def url_img_token(token): # pragma: no cover
    url = '{0}?token={1}'.format(base_url('contrib/verificar-assinatura'), token)
    return qrcode(url, '96x96')

def url_verificador(): # pragma: no cover
    return base_url('contrib/verificar-assinatura')

def qrcode(value, size="128x128"):
    google_url = "http://chart.apis.google.com/chart?cht=qr&chs={0}&chl={1}&chld=L|0".format(size, value)
    alternate_url = "https://api.qrserver.com/v1/create-qr-code/?size={0}&data={1}".format(size, value)

    try:
        response = requests.head(google_url, timeout=5)
        if response.status_code == 200:
            return google_url
        else:
            return alternate_url
    except requests.RequestException:
        return alternate_url

def base_url(value):
    protocolo = 'http' if config.DOMINIO_ATUAL == 'localhost:8000' else 'https'
    return "{0}://{1}/{2}".format(protocolo, config.DOMINIO_ATUAL, value)
