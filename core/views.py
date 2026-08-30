from django.db import IntegrityError, transaction
from django.shortcuts import render
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Magia, Personagem
from .serializers import MagiaSerializer, PersonagemSerializer, RegisterSerializer
from .services import fetch_spell_from_dnd_api


@extend_schema(
    tags=["auth"],
    summary="Cria uma nova conta",
    description=(
        "Endpoint público — não exige token. Cria um usuário novo. "
        "Depois de registrar, use POST /api/auth/token/ para obter o par de tokens JWT."
    ),
    request=RegisterSerializer,
    responses={201: RegisterSerializer, 400: dict},
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"id": user.id, "username": user.username},
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=extend_schema(tags=["personagens"], summary="Lista os personagens do usuário autenticado"),
    create=extend_schema(tags=["personagens"], summary="Cria um novo personagem"),
    retrieve=extend_schema(tags=["personagens"], summary="Detalha um personagem"),
    update=extend_schema(tags=["personagens"], summary="Atualiza um personagem (completo)"),
    partial_update=extend_schema(tags=["personagens"], summary="Atualiza um personagem (parcial)"),
    destroy=extend_schema(tags=["personagens"], summary="Remove um personagem"),
)
class PersonagemViewSet(viewsets.ModelViewSet):
    """CRUD completo para personagens."""

    serializer_class = PersonagemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Personagem.objects.filter(usuario=self.request.user)


@extend_schema_view(
    list=extend_schema(tags=["magias"], summary="Lista as magias do usuário autenticado"),
    create=extend_schema(
        tags=["magias"],
        summary="Busca uma magia na D&D 5e API e adiciona ao grimório",
        description=(
            "O campo `fonte_api` é o **slug** da magia na D&D 5e API "
            "(ex: `fireball`, `magic-missile`), não um nome livre. "
            "A busca é feita por slug exato; se não existir, retorna 404."
        ),
        examples=[
            OpenApiExample(
                "Adicionar Bola de Fogo",
                value={"fonte_api": "fireball", "personagem": 1},
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(tags=["magias"], summary="Detalha uma magia"),
    update=extend_schema(tags=["magias"], summary="Atualiza uma magia (completo)"),
    partial_update=extend_schema(tags=["magias"], summary="Atualiza uma magia (parcial)"),
    destroy=extend_schema(tags=["magias"], summary="Remove uma magia do grimório"),
)
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

            with transaction.atomic():
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


def pagina_personagens(request):
    """Renderiza a página HTML com a lista de personagens e suas magias."""
    personagens_do_banco = Personagem.objects.prefetch_related("magias").all()
    return render(request, "core/lista_personagens.html", {"personagens": personagens_do_banco})
