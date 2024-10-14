from django.core.management.base import BaseCommand, CommandError
from apps.documento.choices import STATUS_PROCESSANDO_ARQUIVO, STATUS_FILA_PROCESSAMENTO
from apps.documento.models import MediaTranscricao
from apps.documento.utils import TanakaUtils
from multiprocessing import Process
import django
from django.db import connection

process = []

def iniciar_transcricao(media_transcricao):
    django.db.close_old_connections()
    tanaka_utils = TanakaUtils(media_transcricao_id=media_transcricao.id)
    # tanaka_utils.transcribe_atrain()
    tanaka_utils.preparar_audio()



def iniciar_async(media_transcricao):
    connection.close()
    th = Process(target=iniciar_transcricao,args=[media_transcricao])
    th.start()
    process.append(th)   

def processar_transcricoes():
    MAX_EXECUTION = 7
    run_transcricoes = MediaTranscricao.objects.filter(status=STATUS_PROCESSANDO_ARQUIVO, ativo=True).count()
    ocupado = run_transcricoes >= MAX_EXECUTION
    if not ocupado:
        size_to_max = MAX_EXECUTION - run_transcricoes
        transcricoes = MediaTranscricao.objects.filter(status=STATUS_FILA_PROCESSAMENTO, ativo=True).order_by('id')[:size_to_max]
        if transcricoes:
            for media_transcricao in transcricoes:
                iniciar_async(media_transcricao)
            
            for proc in process:
                proc.join()

class Command(BaseCommand):
    help = 'Processar Media'

    def handle(self, *args, **options):
        processar_transcricoes()