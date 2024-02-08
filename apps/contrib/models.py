from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.mixins import BaseModel

class Estados(BaseModel):
    nome = models.CharField('Nome', max_length=20)
    sigla = models.CharField('Sigla', max_length=2)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

class Municipios(BaseModel):
    estado = models.ForeignKey('Estados',
                               on_delete=models.DO_NOTHING,
                               related_name='%(class)s_estado')
    nome = models.CharField('Nome', max_length=250)
    codigo = models.CharField('Código', max_length=50)
    municipio_estado = models.CharField('Municipio/UF',
                                        max_length=255,
                                        null=True,
                                        blank=True)
    municipios_responsaveis = models.ManyToManyField('Municipios',
                                                     help_text="""
                                                        Selecione os municipios que serão responsáveis pelos 
                                                        atendimentos deste municipio, caso ele não possua unidade da defensoria""",
                                                     verbose_name='Municipio(s) responsável(is)',
                                                     related_name='%(class)s_municipios_responsaveis',
                                                     blank=True)
    sigla = models.CharField(
        'Sigla',
        max_length=20,
        blank=True,
        null=True,
        unique=True)
    
    def __str__(self):
        return '{}'.format(self.municipio_estado)

    def save(self,
             force_insert=False,
             force_update=False,
             using=None,
             update_fields=None):
        self.municipio_estado = '{} - {}'.format(self.nome, self.estado)
        super(BaseModel, self).save(
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
        )

    class Meta:
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'
        ordering = [
            'municipio_estado',
        ]

class EstadosCivis(BaseModel):
    titulo = models.CharField('Título', max_length=250)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'Estado Civil'
        verbose_name_plural = 'Estados Civis'
        
class Nacionalidades(BaseModel):
    titulo = models.CharField('Título', max_length=250)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'Nacionalidade'
        verbose_name_plural = 'Nacionalidades'

class Escolaridades(BaseModel):
    titulo = models.CharField('Título', max_length=250)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'Escolaridade'
        verbose_name_plural = 'Escolaridades'
        ordering = ['id']

class AssinaturaDocumento(BaseModel):
    token = models.CharField('Token validador', null=True, blank=True, max_length=16)
    
    def __str__(self):
        return self.token
    class Meta:
        verbose_name = 'Certidão Assinatura'
        verbose_name_plural = 'Certidões Assinatura'