from rest_framework.viewsets import ModelViewSet
from apps.documento.models import (
    Chat, 
    Mensagem, 
    MediaTranscricao, 
    Transcricao, 
    AssistenteTopico, 
    AssistenteMensagem,
    AssistentePerfil
)
from apps.documento.api.serializers import (
    ChatSerializer, 
    MensagemSerializer, 
    MediaTranscricaoSerializer, 
    TranscricaoSerializer, 
    AssistenteMensagemSerializer, 
    AssistenteTopicoSerializer,
    AssistentePerfilSerializer
)
import requests
from rest_framework.response import Response
from rest_framework import status
import json
from django_filters import rest_framework as filters
from apps.documento.choices import (
    CHAT_AUTOR_IA, 
    STATUS_FILA_PROCESSAMENTO, 
    STATUS_PROCESSANDO_ARQUIVO, 
    STATUS_FAZENDO_TRANSCRICAO, 
    STATUS_FALHA_PROCESSAMENTO, 
    STATUS_FALHA_TRANSCRICAO,
    STATUS_CONCLUIDO,
    STATUS_OCR_FILA,
    STATUS_OCR_PROCESSANDO,
    STATUS_OCR_FALHA_PROCESSAMENTO,
    STATUS_PDF_FALHA_ENVIO,
    STATUS_OCR_CONCLUIDO,
    CHAT_AUTOR_HUMANO
)
from ..utils import create_questions
from rest_framework.decorators import action
import os
from datetime import datetime, date
from constance import config
from ..utils import get_md5File
from ..assistente import criar_topico, criar_pergunta
from django.utils.html import format_html
from rest_framework.pagination import PageNumberPagination
from config.settings import CHAT_PDF_API_KEY
class ResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100


class ChatFilter(filters.FilterSet):
    class Meta:
        model = Chat
        fields = {
            'criado_por': ['exact'],
            'ativo': ['exact'],
            'status': ['range', 'in'],
        }

class MediaTranscricaoFilter(filters.FilterSet):
    class Meta:
        model = MediaTranscricao
        fields = {
            'criado_por': ['exact'],
            'ativo': ['exact'],
            'status': ['exact'],
        }



class MensagemFilter(filters.FilterSet):
    class Meta:
        model = Mensagem
        fields = {
            'criado_por': ['exact'],
            'is_favorito': ['exact'],
            'texto':['icontains'],
        }

class TranscricaoFilter(filters.FilterSet):
    class Meta:
        model = Transcricao
        fields = {
            'criado_por': ['exact'],
            'texto':['icontains'],
        }


class AssistenteMensagemFilter(filters.FilterSet):
    class Meta:
        model = AssistenteMensagem
        fields = {
            'criado_por': ['exact'],
        }


class AssistenteTopicoFilter(filters.FilterSet):
    class Meta:
        model = AssistenteTopico
        fields = {
            'criado_por': ['exact'],
        }

class AssistentePerfilFilter(filters.FilterSet):
    class Meta:
        model = AssistentePerfil
        fields = {
            'criado_por': ['exact'],
            'ativo': ['exact'],
        }

class ChatViewSet(ModelViewSet):
    queryset = Chat.objects.all().order_by('-criado_em')
    serializer_class = ChatSerializer
    filterset_class = ChatFilter
    pagination_class = ResultsSetPagination
    http_method_names = ['get', 'patch', 'post', 'delete','put']

    def create(self, request, *args, **kwargs):
        string_md5 = get_md5File(request.FILES.get('documento'),fileopen=True)
        search_md5 = Chat.objects.filter(criado_por=request.user,md5_hexdigit=string_md5,ativo=True)
      
        hoje = date.today()
        total_chat_upload_usuario = Chat.objects.filter(criado_por=request.user, criado_em__month=hoje.month, criado_em__year=hoje.year).count()

        if total_chat_upload_usuario > config.DOCUMENTO_LIMITE_UPLOAD_PDF:
            mensagem = f"Você excedeu o limite máximo de {config.DOCUMENTO_LIMITE_UPLOAD_PDF} documentos analizados esse mês." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)
        

        tem_processamento_pendente = Chat.objects.filter(criado_por=request.user, ativo=True, status__in=[
            STATUS_OCR_PROCESSANDO, STATUS_OCR_FILA]).exists()

        if tem_processamento_pendente:
            mensagem = f"Você tem um arquivo em processamento no momento. Aguarde a finalização para enviar outro." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)
        
        if search_md5:
            return Response({'mensagem': format_html(f"Foi identificado que o arquivo já foi pré processado, clique <a href='/documento/chat/?documento={search_md5.first().id}'>aqui!</a> para acessar")}, status=status.HTTP_400_BAD_REQUEST)

        Chat.objects.filter(criado_por=request.user, ativo=True, status__in=[STATUS_OCR_FALHA_PROCESSAMENTO, STATUS_PDF_FALHA_ENVIO]).update(ativo=False)
        Chat.objects.filter(criado_por=request.user, visualizado=False, status=STATUS_OCR_CONCLUIDO).update(visualizado=True)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def resetar_chat(self, request, pk=None):
        chat = Chat.objects.get(id=pk)

        if chat:
            Mensagem.objects.filter(chat=chat).delete()

            headers = {'x-api-key': CHAT_PDF_API_KEY}

            # Remover o chat atigo no Chat PDF
            try:
                data = {'sources': [chat.chatpdf_source_id],}
                
                response = requests.post('https://api.chatpdf.com/v1/sources/delete', json=data, headers=headers)
                response.raise_for_status()
                print('success', response)
            except Exception as e:
                return Response({'mensagem': 'Erro ao deletar o documento do ChatPDF'}, status=status.HTTP_400_BAD_REQUEST)

            # Adicionar novo pdf
            ROOT = os.path.abspath(os.path.dirname(f'media/documento_chat'))
            file_path = '{}/{}'.format(ROOT, chat.documento)
            try:
                with open(file_path, 'rb') as file:
                    files = [('file', ('file', file, 'application/octet-stream'))]
                    response = requests.post('https://api.chatpdf.com/v1/sources/add-file', headers=headers, files=files)

                    if response.status_code == 200:
                        chat.chatpdf_source_id = response.json()['sourceId']
                        chat.save()

                    else:
                        msg_inicial = 'Houve um erro ao processar o PDF'
                        nova_mensagem = Mensagem(texto=msg_inicial, chat_id=chat.id, autor=CHAT_AUTOR_IA, criado_em=datetime.now())
                        nova_mensagem.save()

            except Exception as e:
                return Response({'mensagem': 'Erro ao reenviar o documento para o ChatPDF'}, status=status.HTTP_400_BAD_REQUEST)
            

            return Response({'mensagem': 'Chat resetado'}, status=status.HTTP_200_OK)
        else:
            return Response({'mensagem': 'Chat não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class MensagemViewSet(ModelViewSet):
    queryset = Mensagem.objects.all()
    serializer_class = MensagemSerializer
    filterset_class = MensagemFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']


    def create(self, request, *args, **kwargs):
        chat = request.POST.get('chat')
        texto = request.POST.get('texto')
        autor = request.POST.get('autor')

        total_perguntas_chat = Mensagem.objects.filter(criado_por=request.user, chat_id=chat, autor=CHAT_AUTOR_HUMANO).count()

        if total_perguntas_chat > config.DOCUMENTO_LIMITE_PERGUNTAS_PDF:
            mensagem = f"Você excedeu o limite máximo de {config.DOCUMENTO_LIMITE_PERGUNTAS_PDF} perguntas para este documento." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)

        CQ = create_questions(chat=chat,texto=texto,autor=autor)
        
        return Response({"id": CQ.id, "texto": CQ.texto, "autor": CQ.autor }, status=status.HTTP_201_CREATED)

class MediaTranscricaoViewSet(ModelViewSet):
    queryset = MediaTranscricao.objects.all().order_by('-id')
    serializer_class = MediaTranscricaoSerializer
    filterset_class = MediaTranscricaoFilter
    pagination_class = ResultsSetPagination
    http_method_names = ['get', 'patch', 'post', 'delete','put']

    def create(self, request, *args, **kwargs):
        string_md5 = get_md5File(request.FILES.get('arquivo'),fileopen=True)
        search_md5 = MediaTranscricao.objects.filter(criado_por=request.user,md5_hexdigit=string_md5,ativo=True)


        MediaTranscricao.objects.filter(criado_por=request.user, ativo=True, status__in=[STATUS_FALHA_PROCESSAMENTO, STATUS_FALHA_TRANSCRICAO]).update(ativo=False)
        MediaTranscricao.objects.filter(criado_por=request.user, visualizado=False, status=STATUS_CONCLUIDO).update(visualizado=True)

        hoje = date.today()
        total_video_upload_usuario = MediaTranscricao.objects.filter(criado_por=request.user, criado_em__month=hoje.month, criado_em__year=hoje.year).count()
        tem_processamento_pendente = MediaTranscricao.objects.filter(criado_por=request.user, ativo=True, status__in=[
            STATUS_FILA_PROCESSAMENTO, STATUS_PROCESSANDO_ARQUIVO, STATUS_FAZENDO_TRANSCRICAO]).exists()

        if tem_processamento_pendente:
            mensagem = f"Você tem um video em processamento no momento. Aguarde a finalização para enviar outro." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)

        if total_video_upload_usuario > config.DOCUMENTO_LIMITE_UPLOAD_VIDEO:
            mensagem = f"Você excedeu o limite máximo de {config.DOCUMENTO_LIMITE_UPLOAD_VIDEO} videos analisados esse mês." 
            return Response({"mensagem": mensagem }, status=status.HTTP_400_BAD_REQUEST)

        if search_md5:
            return Response({'mensagem': format_html(f"Foi identificado que o arquivo já foi pré processado, clique <a href='/documento/transcricao/?arquivo={search_md5.first().id}'>aqui!</a> para acessar")}, status=status.HTTP_400_BAD_REQUEST)
        

        return super().create(request, *args, **kwargs)

class TranscricaoViewSet(ModelViewSet):
    queryset = Transcricao.objects.all()
    serializer_class = TranscricaoSerializer
    http_method_names = ['get', 'patch', 'post', 'delete','put']


class AssistenteMensagemViewSet(ModelViewSet):
    queryset = AssistenteMensagem.objects.all()
    serializer_class = AssistenteMensagemSerializer
    filterset_class = AssistenteMensagemFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']
    permission_classes = []


    def create(self, request, *args, **kwargs):
        topico = request.POST.get('topico')
        texto = request.POST.get('texto')
        autor = request.POST.get('autor')
        CQ = criar_pergunta(topico=topico,texto=texto,autor=autor)

        if CQ:
            return Response({"id": CQ.id, "texto": CQ.texto, "autor": CQ.autor }, status=status.HTTP_201_CREATED)
        else:
            return Response({}, status=status.HTTP_201_CREATED)


class AssistenteTopicoViewSet(ModelViewSet):
    queryset = AssistenteTopico.objects.all()
    serializer_class = AssistenteTopicoSerializer
    filterset_class = AssistenteTopicoFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']
    permission_classes = []

    def create(self, request, *args, **kwargs):

        try:
            assistente_id = request.POST.get('assistenteId') if request.POST.get('assistenteId') else None
            topico = criar_topico()

            if topico and topico.id:
                assistente_topico = AssistenteTopico(openia_thread_id=topico.id, assistente_id=assistente_id)
                assistente_topico.save()

                return Response({"id": assistente_topico.id, "mensagens": []}, status=status.HTTP_201_CREATED)
            else:
                return Response({"mensagem": "Não foi possivel criar o chat"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response({{"mensagem": "Erro interno ao criar o chat"}}, status=status.HTTP_400_BAD_REQUEST)



class AssistentePerfilViewSet(ModelViewSet):
    queryset = AssistentePerfil.objects.all()
    serializer_class = AssistentePerfilSerializer
    filterset_class = AssistentePerfilFilter
    http_method_names = ['get', 'patch', 'post', 'delete','put']
    permission_classes = []