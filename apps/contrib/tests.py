from django.test import TestCase, Client
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import Group
from apps.contrib.models import Estados, Municipios, EstadosCivis, Escolaridades, Nacionalidades
from apps.users.models import User

username = 'teste.user'
name = "Teste User"

class EstadosModelTest(TestCase):
    def setUp(self):
        user = User(name=name, username=username,password=settings.USER_PASSWORD_TEST)
        user.save()
        self.user = user

        estado = Estados(nome="Teste",sigla='Teste')
        estado.save()
        self.estado = estado

    def test_estado_str(self):
        self.assertTrue("Teste" in str(self.estado))

class MunicipiosModelTest(TestCase):
    def setUp(self):
        user = User(name=name, username=username,password=settings.USER_PASSWORD_TEST)
        user.save()
        

    def test_municipio_str(self):
        estado = Estados(nome="Teste",sigla='Teste')
        estado.save()

        municipio = Municipios(nome='Municipio teste',estado=estado)
        municipio.save()

        self.assertTrue("Municipio teste - Teste" in str(municipio))

class EstadosCivisModelTest(TestCase):
    def setUp(self):
        user = User(name=name, username=username,password=settings.USER_PASSWORD_TEST)
        user.save()
        

    def test_estados_civis_str(self):
        estados_civil = EstadosCivis(titulo='Estado civil teste')
        estados_civil.save()

        self.assertTrue("Estado civil teste" in str(estados_civil))

class EscolaridadesModelTest(TestCase):
    def setUp(self):
        user = User(name=name, username=username,password=settings.USER_PASSWORD_TEST)
        user.save()
        

    def test_escoladirade_str(self):
        escolaridade = Escolaridades(titulo='Escolaridade teste')
        escolaridade.save()

        self.assertTrue("Escolaridade teste" in str(escolaridade))

class NacionalidadesModelTest(TestCase):
    def setUp(self):
        user = User(name=name, username=username,password=settings.USER_PASSWORD_TEST)
        user.save()
        

    def test_escoladirade_str(self):
        nacionalidade = Nacionalidades(titulo='Nacionalidade teste')
        nacionalidade.save()

        self.assertTrue("Nacionalidade teste" in str(nacionalidade))