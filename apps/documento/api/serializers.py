from rest_framework.serializers import ModelSerializer, SerializerMethodField
from apps.documento.models import Chat, Mensagem, MediaTranscricao, Transcricao


class MensagemSerializer(ModelSerializer):
    
    class Meta:
        model = Mensagem
        fields = '__all__'

class TranscricaoSerializer(ModelSerializer):
    
    class Meta:
        model = Transcricao
        fields = '__all__'

class ChatSerializer(ModelSerializer):
    mensagens = MensagemSerializer(source='mensagem_chat', many=True, read_only=True)

    class Meta:
        model = Chat
        fields = '__all__'

class MediaTranscricaoSerializer(ModelSerializer):
    transcricoes = TranscricaoSerializer(source='transcricao_media_transcricao', many=True, read_only=True)

    class Meta:
        model = MediaTranscricao
        fields = '__all__'


