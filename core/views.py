from django.db import IntegrityError
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Magia, Personagem
from .serializers import MagiaSerializer, PersonagemSerializer
from .services import fetch_spell_from_dnd_api


class PersonagemViewSet(viewsets.ModelViewSet):
    """CRUD completo para personagens."""

    serializer_class = PersonagemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Personagem.objects.filter(usuario=self.request.user)


class MagiaViewSet(viewsets.ModelViewSet):
    """CRUD para magias com dados vindos da API externa."""

    serializer_class = MagiaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Magia.objects.filter(personagem__usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        """Busca a magia na API do D&D e salva como cache local."""
        fonte_api = request.data.get("fonte_api")
        personagem_id = request.data.get("personagem")

        if not fonte_api or not personagem_id:
            return Response(
                {"erro": "Os campos 'fonte_api' e 'personagem' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            personagem = Personagem.objects.get(id=personagem_id, usuario=request.user)
        except Personagem.DoesNotExist:
            return Response(
                {"erro": "Personagem não encontrado ou não pertence a você."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            dados_magia = fetch_spell_from_dnd_api(fonte_api)

            if not dados_magia:
                return Response(
                    {"erro": f"A magia '{fonte_api}' não foi encontrada na base oficial do D&D."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            magia = Magia.objects.create(
                personagem=personagem,
                nome=dados_magia["nome"],
                nivel=dados_magia["nivel"],
                escola=dados_magia["escola"],
                descricao=dados_magia["descricao"],
                fonte_api=dados_magia["fonte_api"],
            )

            serializer = self.get_serializer(magia)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response(
                {"erro": "Este personagem já possui essa magia no grimório."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response({"erro": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
