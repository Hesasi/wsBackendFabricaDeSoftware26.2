"""
Testes de View/endpoint: permissões (JWT), ownership por usuário,
serialização e persistência — usando o service layer sempre mockado
(ver core/tests/test_services.py para os testes do service em si).
"""
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import Magia, Personagem


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def usuario(db):
    return User.objects.create_user(username="elandril", password="senha-forte-123")


@pytest.fixture
def outro_usuario(db):
    return User.objects.create_user(username="brunhilda", password="outra-senha-123")


@pytest.fixture
def auth_client(api_client, usuario):
    api_client.force_authenticate(user=usuario)
    return api_client


@pytest.fixture
def personagem(db, usuario):
    return Personagem.objects.create(usuario=usuario, nome="Elandril", classe="Mago", nivel=7)


@pytest.mark.django_db
class TestPermissoes:
    def test_listar_personagens_sem_autenticacao_retorna_401(self, api_client):
        response = api_client.get("/api/personagens/")
        assert response.status_code == 401

    def test_listar_personagens_autenticado_retorna_200(self, auth_client):
        response = auth_client.get("/api/personagens/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestOwnershipPersonagem:
    def test_usuario_nao_ve_personagem_de_outro_usuario(
        self, auth_client, outro_usuario
    ):
        Personagem.objects.create(
            usuario=outro_usuario, nome="Sombra", classe="Ladino", nivel=3
        )
        response = auth_client.get("/api/personagens/")
        nomes = [p["nome"] for p in response.data["results"]]
        assert "Sombra" not in nomes

    def test_criar_personagem_associa_usuario_autenticado_automaticamente(
        self, auth_client, usuario
    ):
        response = auth_client.post(
            "/api/personagens/",
            {"nome": "Brunhilda", "classe": "Clériga", "nivel": 5},
            format="json",
        )
        assert response.status_code == 201
        criado = Personagem.objects.get(nome="Brunhilda")
        assert criado.usuario == usuario


@pytest.mark.django_db
class TestCriacaoDeMagia:
    @patch("core.views.fetch_spell_from_dnd_api")
    def test_criar_magia_com_sucesso(self, mock_fetch, auth_client, personagem):
        mock_fetch.return_value = {
            "nome": "Bola de Fogo",
            "nivel": 3,
            "escola": "Evocação",
            "descricao": "Uma explosão de fogo.",
            "fonte_api": "fireball",
        }

        response = auth_client.post(
            "/api/magias/",
            {"fonte_api": "fireball", "personagem": personagem.id},
            format="json",
        )

        assert response.status_code == 201
        assert Magia.objects.filter(personagem=personagem, fonte_api="fireball").exists()

    def test_criar_magia_sem_campos_obrigatorios_retorna_400(self, auth_client):
        response = auth_client.post("/api/magias/", {}, format="json")
        assert response.status_code == 400

    def test_criar_magia_para_personagem_de_outro_usuario_retorna_404(
        self, auth_client, outro_usuario
    ):
        personagem_alheio = Personagem.objects.create(
            usuario=outro_usuario, nome="Sombra", classe="Ladino", nivel=3
        )
        response = auth_client.post(
            "/api/magias/",
            {"fonte_api": "fireball", "personagem": personagem_alheio.id},
            format="json",
        )
        assert response.status_code == 404

    @patch("core.views.fetch_spell_from_dnd_api")
    def test_magia_inexistente_na_api_externa_retorna_404(
        self, mock_fetch, auth_client, personagem
    ):
        mock_fetch.return_value = None

        response = auth_client.post(
            "/api/magias/",
            {"fonte_api": "magia-que-nao-existe", "personagem": personagem.id},
            format="json",
        )

        assert response.status_code == 404

    @patch("core.views.fetch_spell_from_dnd_api")
    def test_falha_da_api_externa_retorna_502(self, mock_fetch, auth_client, personagem):
        mock_fetch.side_effect = Exception("Serviço de magias indisponível no momento.")

        response = auth_client.post(
            "/api/magias/",
            {"fonte_api": "fireball", "personagem": personagem.id},
            format="json",
        )

        assert response.status_code == 502

    @patch("core.views.fetch_spell_from_dnd_api")
    def test_magia_duplicada_para_o_mesmo_personagem_retorna_400(
        self, mock_fetch, auth_client, personagem
    ):
        mock_fetch.return_value = {
            "nome": "Bola de Fogo",
            "nivel": 3,
            "escola": "Evocação",
            "descricao": "Uma explosão de fogo.",
            "fonte_api": "fireball",
        }

        primeira = auth_client.post(
            "/api/magias/",
            {"fonte_api": "fireball", "personagem": personagem.id},
            format="json",
        )
        segunda = auth_client.post(
            "/api/magias/",
            {"fonte_api": "fireball", "personagem": personagem.id},
            format="json",
        )

        assert primeira.status_code == 201
        assert segunda.status_code == 400
        assert Magia.objects.filter(personagem=personagem, fonte_api="fireball").count() == 1
