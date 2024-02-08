from rest_framework.serializers import ModelSerializer
from apps.users.models import UserPreferencias, CredenciaisUsuario
from apps.core.utils import core_encrypt

class UserPreferenciasSerializer(ModelSerializer):
    class Meta:
        model = UserPreferencias
        fields = '__all__'

class CredenciaisUsuarioSerializer(ModelSerializer): # pragma: no cover
    class Meta:
        model = CredenciaisUsuario
        fields = '__all__'

    def update(self, instance, validated_data):
        credencial = super().update(instance, validated_data)

        password = validated_data.get('password')

        if password:
            credencial.password = core_encrypt(password)
            credencial.save()

        return credencial