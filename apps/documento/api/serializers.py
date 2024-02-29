from rest_framework.serializers import ModelSerializer, SerializerMethodField
from apps.documento.models import Chat, Mensagem


class MensagemSerializer(ModelSerializer):
    
    class Meta:
        model = Mensagem
        fields = '__all__'

class ChatSerializer(ModelSerializer):
    mensagens = MensagemSerializer(source='mensagem_chat', many=True, read_only=True)

    class Meta:
        model = Chat
        fields = '__all__'


