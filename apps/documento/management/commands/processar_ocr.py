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
from apps.documento.utils import martinha_ocupada, tanaka_ocupado
from constance import config
from django.conf import settings

process = []

def iniciar_ocr(chat,is_martinha):
    django.db.close_old_connections()
    martinha_utils = MartinhaUtils(chat_id=chat.id,is_martinha=is_martinha)
    martinha_utils.preparar_ocr_pdf()

def iniciar_async(chat,is_martinha):
    connection.close()
    th = Process(target=iniciar_ocr,args=[chat,is_martinha])
    th.start()
    process.append(th)
    
def processar_ocr():
    init = True
    is_martinha = True
    ocupado, run_documents_martinha, run_documents_tanaka = martinha_ocupada()
    max_execution = config.MARTINHA_NUM_MAX_EXECUTION - run_documents_martinha
    if settings.IS_TANAKA:
        init = False
        tanaka_ocupada, run_transcricoes_tanaka, run_transcricoes_martinha = tanaka_ocupado()
        tanaka_size_to_max = config.TANAKA_NUM_MAX_EXECUTION - run_transcricoes_tanaka
        if not tanaka_ocupada and tanaka_size_to_max == config.TANAKA_NUM_MAX_EXECUTION:
            init = True
            max_execution = config.MARTINHA_NUM_MAX_EXECUTION_LOAD_BALANCE - run_documents_tanaka
            is_martinha = False

    if not ocupado and init:
        chats = Chat.objects.filter(status=STATUS_OCR_FILA, ativo=True).order_by('id')[:max_execution]
        if chats:
            for chat in chats:
                iniciar_async(chat,is_martinha)
            
            for proc in process:
                proc.join()

class Command(BaseCommand):
    help = 'Processar OCR'

    def handle(self, *args, **options):
        processar_ocr()
