from django.core.management.base import BaseCommand, CommandError
from apps.documento.choices import STATUS_PROCESSANDO_ARQUIVO, STATUS_FILA_PROCESSAMENTO
from apps.documento.models import MediaTranscricao
from apps.documento.utils import preparar_audio

def processar_transcricoes():
    ocupado = MediaTranscricao.objects.filter(status=STATUS_PROCESSANDO_ARQUIVO, ativo=True).exists()
    print('Executando ......')
    if not ocupado:
        transcricao = MediaTranscricao.objects.filter(status=STATUS_FILA_PROCESSAMENTO, ativo=True).order_by('id').first()
        if transcricao:
            print('Processando...')
            preparar_audio(transcricao.id)


class Command(BaseCommand):
    help = 'Processar Media'

    def handle(self, *args, **options):
        processar_transcricoes()
