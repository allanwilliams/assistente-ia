from django.core.management.base import BaseCommand
from apps.documento.choices import (
    STATUS_OCR_FILA,
    STATUS_OCR_PROCESSANDO
)
from apps.documento.models import Chat
from apps.documento.utils import MartinhaUtils
from multiprocessing import Process
import django
from django.db import connection

process = []

def iniciar_ocr(chat):
    django.db.close_old_connections()
    martinha_utils = MartinhaUtils(chat_id=chat.id)
    martinha_utils.preparar_ocr_pdf()

def iniciar_async(chat):
    connection.close()
    th = Process(target=iniciar_ocr,args=[chat])
    th.start()
    process.append(th)
    

def processar_ocr():
    MAX_EXECUTION = 10
    run_documents = Chat.objects.filter(status=STATUS_OCR_PROCESSANDO, ativo=True).count()
    ocupado = run_documents >= MAX_EXECUTION
    if not ocupado:
        size_to_max = MAX_EXECUTION - run_documents
        chats = Chat.objects.filter(status=STATUS_OCR_FILA, ativo=True).order_by('id')[:size_to_max]
        if chats:
            for chat in chats:
                iniciar_async(chat)
            
            for proc in process:
                proc.join()

class Command(BaseCommand):
    help = 'Processar OCR'

    def handle(self, *args, **options):
        processar_ocr()
