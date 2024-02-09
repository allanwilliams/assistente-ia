from rest_framework.viewsets import ModelViewSet
from apps.documento.models import Chat, Mensagem
from apps.documento.api.serializers import ChatSerializer, MensagemSerializer



class ChatViewSet(ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    http_method_names = ['get', 'patch', 'post', 'delete','put']
    

class MensagemViewSet(ModelViewSet):
    queryset = Mensagem.objects.all()
    serializer_class = MensagemSerializer
    http_method_names = ['get', 'patch', 'post', 'delete','put']