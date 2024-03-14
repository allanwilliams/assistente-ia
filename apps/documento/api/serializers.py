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

    def update(self, instance, validated_data):
        request = self.context.get('request')
        replace_all = request.POST.get('replaceAll')
        
        if replace_all == 'true':
            speaker = validated_data.get('speaker')
            Transcricao.objects.filter(media_transcricao_id=instance.media_transcricao.id,speaker=instance.speaker).update(speaker=speaker)
        
        return super().update(instance, validated_data)

class ChatSerializer(ModelSerializer):
    mensagens = MensagemSerializer(source='mensagem_chat', many=True, read_only=True)

    class Meta:
        model = Chat
        fields = '__all__'

class MediaTranscricaoSerializer(ModelSerializer):
    transcricoes = TranscricaoSerializer(source='transcricao_media_transcricao', many=True, read_only=True)
    status_str = SerializerMethodField()

    def get_status_str(self, obj):
        return obj.get_status_display() if obj.status else None

    class Meta:
        model = MediaTranscricao
        fields = '__all__'


