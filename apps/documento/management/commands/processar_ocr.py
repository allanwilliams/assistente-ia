from django.core.management.base import BaseCommand
from apps.documento.choices import (
    STATUS_OCR_FILA,
    STATUS_OCR_PROCESSANDO
)
from apps.documento.models import Chat
from apps.documento.utils import MartinhaUtils

def processar_ocr():
    ocupado = Chat.objects.filter(status=STATUS_OCR_PROCESSANDO, ativo=True).count() >= 1
    print('Executando OCR....')
    if not ocupado:
        chat = Chat.objects.filter(status=STATUS_OCR_FILA, ativo=True).order_by('id').first()
        if chat:
            print('Processando OCR...')
            martinha_utils = MartinhaUtils(chat_id=chat.id)
            martinha_utils.preparar_ocr_pdf()


class Command(BaseCommand):
    help = 'Processar OCR'

    def handle(self, *args, **options):
        processar_ocr()
