from rest_framework.serializers import ModelSerializer

class GenericAllSerializer(ModelSerializer):
    class Meta:
        model = None
        fields = '__all__'
        depth = 2