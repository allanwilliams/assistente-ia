from django.test import TestCase, Client
from django.conf import settings
from django.utils import timezone
from apps.users.models import User
from apps.certidao_localizacao.models import Certidao
from apps.contrib.helpers import get_hash
from apps.contrib.models import Estados, AssinaturaDocumento
from apps.core.encrypt_url_utils import encrypt

username = 'teste.user'
name = "Teste User"
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
assinar_salvar_url = '/certidao_localizacao/assinar-salvar'
verificar_assinatura_url = '/certidao_localizacao/verificar-assinatura'

class CertidaoTest(TestCase):
    def setUp(self):
        settings.USE_FUSIONAUTH = False
        self.client = Client()

        user = User(name='name', username=username,is_staff=True,is_superuser=True)
        user.set_password(settings.USER_PASSWORD_TEST)
        user.save()

        estado = Estados(nome='Teste', sigla="teste")
        estado.save()

        self.user = user
        self.client.force_login(user=user)        

    def test_assinatura_str(self):
        token_validador = get_hash()
        dic_assinatura = {
            'token': token_validador,
            'criado_em': timezone.now()
        }
        assinatura = AssinaturaDocumento(**dic_assinatura)
        assinatura.save()
        
        self.assertTrue(token_validador in str(assinatura))
        
    def test_assinar(self):
        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            criado_por=self.user
        )
        certidao.save()
        data = {
            'usuario_senha': settings.USER_PASSWORD_TEST,
            'certidao': encrypt(certidao.id),
            'lat': 52.509669,
            'long': 13.376294
        }
        response = self.client.post(assinar_salvar_url, data,HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)

    def test_assinar_invalida(self):
        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            criado_por=self.user
        )
        certidao.save()
        hash_id = encrypt(certidao.id)
        data = {
            'usuario_senha': 'invalida',
            'certidao': hash_id,
            'lat': 0,
            'long': 0
        }
        response = self.client.post(assinar_salvar_url, data,HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.url, f'/certidao_localizacao/assinar-certidao?certidao={hash_id}')

    def test_assinar_lat_long_invalida(self):
        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            criado_por=self.user
        )
        certidao.save()
        hash_id = encrypt(certidao.id)
        data = {
            'usuario_senha': 'invalida',
            'certidao': hash_id,
        }
        response = self.client.post(assinar_salvar_url, data,HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.url, f'/certidao_localizacao/assinar-certidao?certidao={hash_id}')
    
    def test_verificar_assinatura_get(self):
        token_validador = get_hash()
        dic_assinatura = {
            'token': token_validador,
            'criado_em': timezone.now()
        }
        assinatura = AssinaturaDocumento(**dic_assinatura)
        assinatura.save()
        
        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            assinatura=assinatura,
            criado_por=self.user
        )
        certidao.save()

        response = self.client.get(verificar_assinatura_url, {'token': token_validador},HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)
    
    def test_verificar_assinatura_get_sem_token(self):
        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            criado_por=self.user
        )
        certidao.save()
        
        response = self.client.get(verificar_assinatura_url, HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)

    def test_verificar_assinatura_post(self):
        token_validador = get_hash()
        dic_assinatura = {
            'token': token_validador,
            'criado_em': timezone.now()
        }
        assinatura = AssinaturaDocumento(**dic_assinatura)
        assinatura.save()

        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            assinatura=assinatura,
            criado_por=self.user
        )
        certidao.save()
        
        response = self.client.post(verificar_assinatura_url, {'token': token_validador},HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)

    def test_verificar_assinatura_post_doc_nao_assinado(self):
        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            criado_por=self.user
        )
        certidao.save()
        
        token_validador = get_hash()
        
        response = self.client.post(verificar_assinatura_url, {'token': token_validador},HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)

    def test_assinar_certidao_assinada(self):
        token_validador = get_hash()
        dic_assinatura = {
            'token': token_validador,
            'criado_em': timezone.now()
        }
        assinatura = AssinaturaDocumento(**dic_assinatura)
        assinatura.save()

        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            assinatura=assinatura,
            criado_por=self.user
        )
        certidao.save()
        

        response = self.client.get('/certidao_localizacao/assinar-certidao', {'certidao': encrypt(certidao.id)},HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)

    def test_assinar_certidao_nao_assinada(self):
        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            criado_por=self.user
        )
        certidao.save()
        
        response = self.client.get('/certidao_localizacao/assinar-certidao', {'certidao': encrypt(certidao.id)},HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)

    def test_admin_certidao(self):
        certidao = Certidao(
            municipio="Fortaleza",
            data_hora=timezone.now(),
            criado_por=self.user
        )
        certidao.save()
        
        response = self.client.get('/admin/certidao_localizacao/certidao/',HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)

    def test_admin_certidao_add_view(self):
        response = self.client.get('/admin/certidao_localizacao/certidao/add/',HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200,response)
        