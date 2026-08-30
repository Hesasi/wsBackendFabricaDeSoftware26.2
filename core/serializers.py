from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Magia, Personagem


class RegisterSerializer(serializers.ModelSerializer):
    """Cria uma nova conta de usuário (endpoint público de registro)."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["username", "email", "password"]
        extra_kwargs = {"email": {"required": False}}

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Esse nome de convocador já está em uso.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


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
