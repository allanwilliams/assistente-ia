from statistics import mode
from django.db import models
from apps.core.mixins import BaseModel
from django.conf import settings
from apps.contrib.models import Estados, AssinaturaDocumento

# Create your models here.
class Certidao(BaseModel):
    ip = models.CharField(max_length=20,null=True,blank=True)

    municipio = models.CharField(max_length=500,null=True,blank=True)

    data_hora = models.DateTimeField(blank=True, null=True)

    assinatura = models.ForeignKey(
        AssinaturaDocumento,
        verbose_name=("Assinatura Documento"),
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )

    latitude = models.CharField(blank=True, null=True, max_length=50)

    longitude = models.CharField(blank=True, null=True, max_length=50)
    
    estado = models.ForeignKey(
        Estados,
        verbose_name=("Estado"),
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )

    crypted_fields = ['municipio',]

    class Meta:
        verbose_name = 'Certidão'
        verbose_name_plural = 'Certidões'