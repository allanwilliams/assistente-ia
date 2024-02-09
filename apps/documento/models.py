from django.db import models
from apps.core.mixins import BaseModel
from apps.documento.choices import CHOICES_CHAT_AUTOR, CHAT_AUTOR_IA
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.

class Chat(BaseModel):
    titulo = models.CharField('Titulo', max_length=255)
    documento = models.FileField('Documento', upload_to='documento_chat')

    def __str__(self) -> str:
        return f'{self.id}'


@receiver(post_save, sender=Chat)
def criar_mensagens_chat(sender, instance, **kwargs):
    if instance:
        tem_mensagens = Mensagem.objects.filter(chat_id=instance.id).exists()

        if not tem_mensagens:
            try:
                nova_mensagem = Mensagem(texto="Bem vindo ao dede chat", chat_id=instance.id, autor=CHAT_AUTOR_IA, criado_em=datetime.now())
                nova_mensagem.save()
            except Exception as e:
                print('erro', e)





class Mensagem(BaseModel):
    texto = models.TextField('mensagem')
    chat = models.ForeignKey(
        Chat,
        on_delete=models.PROTECT,
        related_name='%(class)s_chat',
    )
    autor = models.IntegerField('Autor', choices=CHOICES_CHAT_AUTOR)

    def __str__(self) -> str:
        return f'{self.chat} - {self.get_autor_display()}'
    
    class Meta:
        verbose_name_plural = 'Mensagens'

