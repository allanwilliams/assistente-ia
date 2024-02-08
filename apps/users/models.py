from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.utils.translation import ugettext_lazy as _
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, pre_save
from django.conf import settings
from django_currentuser.middleware import get_current_authenticated_user
from django.utils import timezone
from django.core import serializers
from django.contrib.auth.models import Group
from apps.users.choices import  CHOICES_SEXO_USER
from apps.core.mixins import BaseModel
from apps.core.utils import core_encrypt,core_decrypt
import json
import requests

Group.cols = {
    'name': 12,
    'permissions':12
}

class User(AbstractUser):
    PAPEL_DEFENSOR = 1
    
    cols = {
        'name': 3,
        'papel':3,
        'matricula':3,
        'num_orgao_classe':3,
        'username':4,
        'email': 4,
        'password':4,
        'cpf': 3,
        'first_name': 3,
        'last_name': 3,
        'is_active': 4,
        'is_staff': 4,
        'is_superuser': 4,
        'groups': 12,
        'user_permissions': 12,
    }
  
    name = CharField(_("Nome Completo"), blank=True, max_length=255)

    papel = models.ForeignKey(
        'users.Papeis',
        verbose_name='Papeis',
        on_delete=models.PROTECT,
        related_name='%(class)s_papel',
        null=True,
        db_index=True,
    )

    matricula = models.CharField(
        'Matricula',
        max_length=11,
        help_text="Obrigatório para cadastro de defensores",
        unique=True,
        blank=True,
        null=True)
    
    num_orgao_classe = CharField(_("Número do Órgão de Classe"),
                                 blank=True,
                                 null=True,
                                 max_length=255)

    cpf = models.CharField('CPF', max_length=500, unique=True, null=True, blank=True)

   
    sexo = models.IntegerField(_("Sexo"), choices=CHOICES_SEXO_USER,
                               default=0,)
    user_str = models.CharField('User String',
                                blank=True, null=True, max_length=200)
    
    fusionauth_user_id = models.CharField('FusionAuth user ID',max_length=50,blank=True, null=True)

    foto = models.ImageField('Foto', upload_to='user_foto', blank=True, null=True)

    nacionalidade = models.ForeignKey(
        'contrib.Nacionalidades',
        on_delete=models.PROTECT,
        related_name='%(class)s_nacionalidade',
        blank=True,
        null=True,
        default=None
    )

    escolaridade = models.ForeignKey('contrib.Escolaridades',on_delete=models.PROTECT,
        related_name='%(class)s_escolaridade',
        null=True, blank=True)
    
    endereco = models.CharField(
        'Endereço',
        max_length=200,
        blank=True,
        null=True,
    )

    numero = models.CharField(
        'Número',
        max_length=11,
        blank=True,
        null=True,
    )

    complemento = models.CharField(
        'Complemento',
        max_length=200,
        blank=True,
        null=True,
    )

    cep = models.CharField(
        'CEP',
        max_length=200,
        blank=True,
        null=True,
    )

    bairro = models.CharField(
        'Bairro',
        max_length=200,
        blank=True,
        null=True,
    )

    telefone = models.CharField(
        'Telefone',
        max_length=200,
        blank=True,
        null=True,
    )

    municipio = models.ForeignKey(
        'contrib.Municipios',
        on_delete=models.PROTECT,
        related_name='%(class)s_municipios',
        blank=True,
        null=True
    )

    estado_civil = models.ForeignKey(
        'contrib.EstadosCivis',
        on_delete=models.PROTECT,
        related_name='%(class)s_estado_civil',
        blank=True,
        null=True,
    )

    estado = models.ForeignKey(
        "contrib.Estados",
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_usuarioestado',
        null=True
    )

    rg = models.CharField(
        'RG',
        max_length=200,
        blank=True,
        null=True,
    )

    nome_mae = models.CharField(
        'Nome da Mãe',
        max_length=200,
        blank=True,
        null=True,
    )

    data_nascimento = models.DateField('Data de nascimento', null=True, blank=True)

    email_alternativo = models.EmailField('Email alternativo', blank=True, null=True)

    crypted_fields = ['cpf',]

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None):
        if self.name:
            if ' ' in self.name:
                name = self.name.split(' ')
            else:
                name = [self.name, self.name]
            if not self.first_name:
                self.first_name = name[0]
            if not self.last_name:
                self.last_name = name[-1]
        
        if self.id and self.first_name:
            self.user_str = '{:08n} {} {} ({})'.format(self.id, self.first_name, self.last_name,self.username)
        
        if hasattr(self,'crypted_fields'):
            for crypted_field in self.crypted_fields:
                new_value = core_encrypt(core_decrypt(getattr(self, crypted_field)))
                setattr(self, crypted_field, new_value)

        super(User, self).save(
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
        )
        if settings.USE_FUSIONAUTH and self.fusionauth_user_id: # pragma: no cover
            self.save_userdata()
            self.save_userfusionauth()

    @classmethod
    def from_db(cls, db, field_names, values):
        if hasattr(cls,'crypted_fields'):
            for crypted_field in cls.crypted_fields:
                index = field_names.index(crypted_field)
                new_value = core_decrypt(values[index])
                new_values = list(values)
                new_values[index] = new_value
                values = tuple(new_values)
        return super().from_db(db, field_names, values)
        
    def save_userdata(self): # pragma: no cover
        my_json = json.loads(self.model_to_json())[0]['fields']
        for field in list(my_json):
            if field not in self.userdata_list_fields():
                del my_json[field]
        
        from apps.django_sso_app.helpers import update_userdata
        update_userdata(my_json,self.fusionauth_user_id)

    def save_userfusionauth(self): # pragma: no cover
        from apps.django_sso_app.helpers import update_user_by_id
        data = {
            "firstName": self.first_name,
            "fullName": self.name,
            "lastName": self.last_name
        }
        update_user_by_id(data,self.fusionauth_user_id)

    def test_fusionauth_password(self,password): # pragma: no cover
        api_url = settings.FUSIONAUTH_HOST + '/api/login'
        data_user = {
            'loginId': self.email,
            'password': password
        }

        headers = { 'Content-Type': 'application/json', 'Authorization': settings.FUSIONAUTH_USER_API_KEY }
        response = requests.post(url=api_url,json=data_user,headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            if user_data['token']:
                return True
        return False


    def model_to_json(self): # pragma: no cover
        return serializers.serialize('json', [self])

    def __str__(self):
        return '{:08n} {} {} ({})'.format(self.id, self.first_name or '', self.last_name or '', self.username)

    def userdata_list_fields(self): # pragma: no cover
        return [
            'cpf','rg'
        ]

    def is_defensor(self):
        if self.papel_id in (self.PAPEL_DEFENSOR,):
            return True
        else:
            return False
    
    def get_user_preferencias(self):
        preferencias_obj = {}
        if self:
            preferencias = UserPreferencias.objects.filter(user=self)
            tipos = UserPreferencias.Tipos
            

            for tipo in tipos:
                preferencias_obj[tipo.name] = {
                    'id': tipo.value,
                    'label':tipo.label,
                    'value':preferencias.filter(preferencia=tipo).first() or False
                }
        return preferencias_obj
    
    def get_user_credenciais(self):
        credenciais_obj = {}
        if self:
            credenciais = CredenciaisUsuario.objects.filter(user=self)
            sistemas = CredenciaisUsuario.SistemasCredenciais
            

            for sistema in sistemas:
                credenciais_obj[sistema.name] = {
                    'id': sistema.value,
                    'label':sistema.label,
                    'value':credenciais.filter(sistema=sistema).first() or False
                }
        return credenciais_obj
    

@receiver(post_save, sender=User)
def create_app_user_str(sender, instance, created, **kwargs):
    if created:
        instance.user_str = '{:08n} {} {} ({})'.format(instance.id, instance.first_name, instance.last_name,instance.username)
        instance.save() 

class Papeis(BaseModel):
    titulo = models.CharField(
        'Título',
        max_length=500,
    )

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'Papel'
        verbose_name_plural = 'Papeis'
        ordering = [
            'titulo',
        ]


class Defensores(BaseModel):
    nome = models.CharField('Nome', max_length=150)
    matricula = models.CharField('Matricula', max_length=11)
    cpf = models.CharField('CPF', max_length=11)
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_usuario',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Defensores'
        verbose_name_plural = 'Defensores'
        ordering = ['nome', ]


class DefensoresLotacoes(BaseModel):
    cols = {
        'defensor': 3,
        'especie': 2,
        'data_inicio': 2,
        'data_termino': 2,
        'defensor_matricula': 2,
        'local_atuacao': 4,
        'defensor_cpf': 2,
        'defensor_email': 2,
        'user': 2,
        'nucleo': 2,
        'defensoria': 4,
        'tipo': 2,
        'ativo': 1,
        'origem_id': 2,
        'origem': 4,
        'titularidade_designacao': 2,
        'defensoreslocacoes_str': 4,
        'criado_por': 4,
        'criado_em': 2,
        'modificado_por': 4,
        'modificado_em': 2
    }

    defensor_nome = models.CharField('Defensor', max_length=255)
    defensor_matricula = models.CharField('Matricula', max_length=11, db_index=True)
    defensor_cpf = models.CharField('CPF', max_length=11)
    defensor_email = models.CharField('E-mail', max_length=255, null=True)
    defensoria = models.CharField('Defensoria', max_length=255)
    tipo = models.CharField('Tipo', max_length=50)
    titularidade_designacao = models.CharField('Titularidade ou Designação',
                                               max_length=50)
    origem = models.CharField('Origem', max_length=255)
    origem_id = models.IntegerField('Identificador da Origem')
    data_inicio = models.DateField(
        'Data de Início',
        db_index=True,)
    data_termino = models.DateField(
        'Data de Término',
        null=True,
        blank=True,
        db_index=True,
    )
    nucleo_txt = models.CharField(
        'Núcleo',
        max_length=255,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_usuario',
        null=True,
        blank=True,
        db_index=True,
    )
    defensor = models.ForeignKey(
        Defensores, on_delete=models.PROTECT,
        related_name='%(class)s_defensores',
        verbose_name='Defensor',
        null=True, blank=True,
        db_index=True,)
    defensoreslocacoes_str = models.CharField(
        'Defensor(a)/Defensoria',
        max_length=255,
        null=True,
        blank=True,
    )
    ativo = models.BooleanField('Está ativa?', blank=True, default=True)

    def __str__(self):
       return '{} - {}'.format(self.defensor_nome, self.defensoria)

    def save(self, *args, **kwargs):
        from datetime import datetime
        from django.db.models import Q
        DefensoresLotacoes.objects. \
            exclude(data_inicio__lte=datetime.now()). \
            exclude(Q(data_termino__gte=datetime.now()) | Q(data_termino__isnull=True)). \
            update(ativo=False)
        self.defensoreslocacoes_str = '{} - {}'.format(self.defensor_nome, self.defensoria)
        super(DefensoresLotacoes, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Lotação dos defensores'
        verbose_name_plural = 'Lotações dos defensores'
        ordering = ['-data_inicio', ]

class UserPreferencias(BaseModel):

    class Tipos(models.IntegerChoices):
        MENU_COMPACTO = 1, 'Menu fixo'
    
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='%(class)s_user',
    )

    preferencia = models.IntegerField('Preferência', choices=Tipos.choices)

    class Meta:
        verbose_name = 'Preferência do Usuário'
        verbose_name_plural = 'Preferências dos Usuários'

class TrocaSenhaUsuario(BaseModel):
    user = models.ForeignKey(
        'User',
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_usuario',
        null=True,
        blank=True,
        db_index=True,
    )
    
    password = models.CharField(_('password'), max_length=128)
    
    @receiver(pre_save, sender=User)
    def user_updated(sender, **kwargs):
        if not settings.USE_FUSIONAUTH:
            try:
                user = kwargs.get('instance', None)
                if user and hasattr(user,'pk'):
                        user_old = User.objects.get(pk=user.pk)
                        if user and user_old:
                            if user.password != user_old.password:
                                dict_password = {
                                    'user': user,
                                    'password': user.password,
                                    'criado_em': timezone.now()
                                }
                                grava_senha = TrocaSenhaUsuario(**dict_password)
                                grava_senha.save()
            except Exception:
                pass

class CredenciaisUsuario(BaseModel):
    class SistemasCredenciais(models.IntegerChoices):
        PJE = 1, 'PJE'
        ESAJ = 2, 'ESAJ'
        SEEU = 3, 'SEEU'

    user = models.ForeignKey(
        'User',
        on_delete=models.DO_NOTHING,
        related_name='%(class)s_usuario',
        null=True,
        blank=True,
        db_index=True,
    )

    sistema = models.IntegerField('Sistema', choices=SistemasCredenciais.choices)

    password = models.CharField('password', max_length=128)

    usuario = models.CharField('password', max_length=128, null=True)
