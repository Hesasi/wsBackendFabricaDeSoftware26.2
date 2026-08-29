from rest_framework import serializers

from .models import Magia, Personagem


class MagiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Magia
        fields = ["id", "nome", "nivel", "escola", "descricao", "fonte_api", "personagem"]

        # Esses campos são preenchidos pelo backend, não pelo cliente via Postman.
        read_only_fields = ["nome", "nivel", "escola", "descricao", "personagem"]


class PersonagemSerializer(serializers.ModelSerializer):
    magias = MagiaSerializer(many=True, read_only=True)
    usuario = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Personagem
        fields = ["id", "nome", "classe", "nivel", "usuario", "magias"]
