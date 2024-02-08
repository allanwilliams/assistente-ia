from django.test import TestCase, Client
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import Group
from apps.users.models import User,UserPreferencias, Defensores, Papeis, DefensoresLotacoes
from apps.users.forms import UserCreationForm, ImportarUsuariosForm
from apps.contrib.models import Estados
from io import BytesIO

username = 'teste.user'
name = "Teste User"
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'

class UserModelTest(TestCase):
    def setUp(self):
        user = User(name="Teste User", username=username,password=settings.USER_PASSWORD_TEST)
        user.save()
        self.user = user

        papel = Papeis(id=1,titulo='Defensor')
        papel.save()

        user_defensor = User(name="Teste", username='teste.user.defensor', papel=papel)
        user_defensor.save()

        self.user_defensor = user_defensor

    def test_user_str(self):
        self.assertTrue("Teste User (teste.user)" in str(self.user))

    def test_get_preferencia(self):
        preferencia = UserPreferencias(user=self.user, preferencia=1)
        preferencia.save()

        prefencias = self.user.get_user_preferencias()
        self.assertTrue(len(prefencias) > 0,'Preferências do usuário não carregadas')

    def test_validated_is_defensor(self):
        self.assertTrue(self.user_defensor.is_defensor())
    
    def test_validated_is_not_defensor(self):
        self.assertFalse(self.user.is_defensor())

    def test_troca_senha_usuario(self):
        settings.USE_FUSIONAUTH = False
        self.user.set_password('Dpgeceti@20yy')
        self.user.save()

        self.assertTrue(self.user.check_password('Dpgeceti@20yy'))


class UserFormTest(TestCase):
    def setUp(self):
        user = User(first_name="Teste", last_name="Init", username='teste.init',cpf='00000000000')
        user.save()
        self.user = user

    def test_valid_data(self):
        form = UserCreationForm({
            'username':username,
            'password1': settings.USER_PASSWORD_TEST,
            'password2': settings.USER_PASSWORD_TEST,
        })

        self.assertTrue(form.is_valid())

        usuario = form.save()
        self.assertTrue("(teste.user)" in str(usuario),str(usuario))

    def test_duplicated_username(self):
        form1 = UserCreationForm({
            'username': username,
            'password1': settings.USER_PASSWORD_TEST,
            'password2': settings.USER_PASSWORD_TEST,
        })

        if form1.is_valid():
            form1.save()

        form2 = UserCreationForm({
            'username': username,
            'password1': settings.USER_PASSWORD_TEST,
            'password2': settings.USER_PASSWORD_TEST,
        })

        self.assertFalse(form2.is_valid())

    def test_duplicated_cpf(self):
        '''
            IMPLEMENTAR TESTE DE CPF DUPLICADO
        '''
        pass

class UserImportTest(TestCase):
    def setUp(self):
        settings.USE_FUSIONAUTH = False
        csv = "\nUsuario de importacao;12345678910;XXXXX-X;1;user.importacao;email@email.com;1;True"
        csv_duplicado = "\nUsuario de importacao;12345678910;XXXXX-X;1;user.importacao;email@email.com;1;True\nUsuario de importacao;12345678910;XXXXX-X;1;user.importacao;email@email.com;1;True"
        self.arquivo_csv = InMemoryUploadedFile(
            BytesIO(csv.encode('utf-8')),
            None,
            'arquivo.csv',
            'text/csv',
            len(csv),
            None
        )
        self.arquivo_csv_duplicado = InMemoryUploadedFile(
            BytesIO(csv_duplicado.encode('utf-8')),
            None,
            'arquivo.csv',
            'text/csv',
            len(csv_duplicado),
            None
        )
        self.client = Client()

        user = User(name='name', username=username,password=settings.USER_PASSWORD_TEST,is_staff=True,is_superuser=True)
        user.save()

        self.client.force_login(user=user)

        papel = Papeis(id=1,titulo='Defensor')
        papel.save()

        grupo = Group(id=1,name='Teste')
        grupo.save()
        

    def test_import_user_from_csv(self):
        form = ImportarUsuariosForm(data={},files={'file':self.arquivo_csv})
        self.assertTrue(form.is_valid())

    def test_import_user_duplicado_request(self):
        response = self.client.post('/users/importar-usuarios', {'file': self.arquivo_csv_duplicado},HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200,response)

    def test_import_user_request(self):
        response = self.client.post('/users/importar-usuarios', {'file': self.arquivo_csv},HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200,response)
    
class UserProfileTest(TestCase):
    def setUp(self):
        self.user = User(name='name', username=username,password=settings.USER_PASSWORD_TEST,is_staff=True)
        self.user.save()

        self.estado = Estados(nome='Estado teste')
        self.estado.save()
    
    def test_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(f'/users/perfil/{self.user.id}',HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.status_code, 200)

    def test_post_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(f'/users/perfil/{self.user.id}',{'cpf':'1234567890','estado':self.estado.id},HTTP_USER_AGENT=user_agent)
        self.assertEqual(response.url, f'/users/perfil/{self.user.id}')
        


class PapeisModelTest(TestCase):
    def setUp(self):
        user = User(name='name', username=username,password=settings.USER_PASSWORD_TEST,is_staff=True)
        user.save()

        papel = Papeis(id=1,titulo='Defensor')
        papel.save()
        self.papel = papel

    def test_papel_str(self):
        self.assertTrue('Defensor' in str(self.papel))

class DefensorModelTest(TestCase):
    def test_defensor_str(self):
        user = User(first_name="Teste", last_name="User", username=username)
        user.save()

        defensor = Defensores(nome='teste',matricula='0000',cpf='00000000000',user=user)
        defensor.save()
        self.assertEquals(str(defensor),defensor.nome)

class DefensoresLotacoesModelTest(TestCase):
    def setUp(self):
        user = User(name='name', username=username,password=settings.USER_PASSWORD_TEST,is_staff=True)
        user.save()

        from datetime import datetime
        defensor_lotacao = DefensoresLotacoes(
            defensor_nome='teste',
            defensoria='teste defensoria',
            origem_id=1,
            data_inicio=datetime.today()
        )
        defensor_lotacao.save()

        self.defensor_lotacao = defensor_lotacao
    
    def test_defensores_lotacoes_str(self):
        self.assertEqual('teste - teste defensoria',str(self.defensor_lotacao))
