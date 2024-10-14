from django.core.management.base import BaseCommand, CommandError
import time
from django.db import connection
from apps.documento.models import Chat, MediaTranscricao
from datetime import datetime, timedelta
from constance import config

def remover_arquivos_antigos():
    data_atual = datetime.now()
    data_limite_martinha = data_atual - timedelta(days=config.MARTINHA_NUM_MAX_DAYS_KEEP_FILES)
    data_limite_tanaka = data_atual - timedelta(days=config.TANAKA_NUM_MAX_DAYS_KEEP_FILES)

    chats_antigos = Chat.objects.filter(criado_em__lte=data_limite_martinha).exclude(documento__isnull=True)
    medias_antigas = MediaTranscricao.objects.filter(criado_em__lte=data_limite_tanaka).exclude(arquivo__isnull=True)

    for chat in chats_antigos:
        try: chat.remove_old_file()
        except Exception as e:
            print(e)
            pass
    
    for media in medias_antigas:
        try: media.remove_old_file()
        except Exception as e:
            print(e)
            pass


class Command(BaseCommand):
    help = 'Remover arquivos que ultrapassam os X dias de permanência dentro do sistema'

    def handle(self, *args, **options):
        remover_arquivos_antigos()

