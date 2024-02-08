from django.test import TestCase
from django.conf import settings
from apps.lembrete.models import Lembretes
from apps.lembrete.forms import LembretesForm
from apps.users.models import User

username = 'teste.user'
name = "Teste User"

class LembretesModelTest(TestCase):
    def setUp(self):
        self.user = User(name=name, username=username,password=settings.USER_PASSWORD_TEST)
        self.user.save()
        
        user2 = User(name=name, username=f'{username}2',password=settings.USER_PASSWORD_TEST)
        user2.save()
        self.lembrete = Lembretes(titulo='Lembrete Teste',destinatario=self.user)
        self.lembrete.save()
        self.lembrete.criado_por = user2
        self.lembrete.save()

    def test_str_lembrete(self):
        self.assertTrue("Lembrete Teste" in str(self.lembrete))

    # def test_verifica_origem(self):
    #     self.assertEqual('Recebido',self.lembrete.verifica_origem())

    def test_get_origem(self):
        self.assertTrue(isinstance(self.lembrete.get_origem(),str))

    def test_get_destino(self):
        self.assertTrue(isinstance(self.lembrete.get_destino(),str))

    def test_create_lembrete_proprio(self):
        self.lembrete = Lembretes(titulo='Lembrete Teste')
        self.lembrete.save()

    def test_lembrete_form(self):
        form = LembretesForm({
            'titulo':'Lembrete teste form',
            'destinatario': self.user.id,
            'prioridade':1
        })

        self.assertTrue(form.is_valid(),form.errors)

        lembrete = form.save()
        self.assertTrue("Lembrete teste form" in str(lembrete))
    
    def test_lembrete_exists_form(self):
        form = LembretesForm({
            'titulo':'Lembrete teste form',
            'destinatario': self.user.id,
            'prioridade':1,
        },instance=self.lembrete)

        self.assertTrue(form.is_valid(),form.errors)

        lembrete = form.save()
        self.assertTrue("Lembrete teste form - 00" in str(lembrete),lembrete)