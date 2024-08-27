from django.core.management.base import BaseCommand, CommandError
from apps.documento.choices import STATUS_PROCESSANDO_ARQUIVO, STATUS_FILA_PROCESSAMENTO
from apps.documento.models import MediaTranscricao
from apps.documento.utils import TanakaUtils
from multiprocessing import Process
import django
from django.db import connection
from apps.documento.utils import tanaka_ocupado, martinha_ocupada
from constance import config
from django.conf import settings
import time


process = []

def iniciar_transcricao(media_transcricao,is_tanaka):
    django.db.close_old_connections()
    tanaka_utils = TanakaUtils(media_transcricao_id=media_transcricao.id, is_tanaka=is_tanaka)
    tanaka_utils.preparar_audio()

def iniciar_async(media_transcricao,is_tanaka):
    connection.close()
    th = Process(target=iniciar_transcricao,args=[media_transcricao,is_tanaka])
    th.start()
    process.append(th)   

def processar_transcricoes():
    if settings.IS_MARTINHA:
        time.sleep(15)
    init = True
    is_tanaka = True
    ocupado, run_transcricoes_tanaka, run_transcricoes_martinha = tanaka_ocupado()
    max_execution = config.TANAKA_NUM_MAX_EXECUTION - run_transcricoes_tanaka
    if settings.IS_MARTINHA:
        init = False
        martinha_ocupado, run_documents_martinha, run_documents_tanaka = martinha_ocupada()
        martinha_size_to_max = config.MARTINHA_NUM_MAX_EXECUTION - run_documents_martinha
        if not martinha_ocupado and martinha_size_to_max == config.MARTINHA_NUM_MAX_EXECUTION:
            init = True
            max_execution = config.TANAKA_NUM_MAX_EXECUTION_LOAD_BALANCE - run_transcricoes_martinha
            is_tanaka = False

    if not ocupado and init:
        transcricoes = MediaTranscricao.objects.filter(status=STATUS_FILA_PROCESSAMENTO, ativo=True).order_by('id')[:max_execution]
        if transcricoes:
            for media_transcricao in transcricoes:
                iniciar_async(media_transcricao,is_tanaka)
            
            for proc in process:
                proc.join()

class Command(BaseCommand):
    help = 'Processar Media'

    def handle(self, *args, **options):
        processar_transcricoes()