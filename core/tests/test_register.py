"""
Testes do endpoint de registro (POST /api/auth/register/).
"""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestRegistro:
    def test_criar_conta_com_sucesso(self, api_client):
        response = api_client.post(
            "/api/auth/register/",
            {"username": "elandril", "email": "elandril@grimorio.com", "password": "SenhaForte123!"},
            format="json",
        )
        assert response.status_code == 201
        assert User.objects.filter(username="elandril").exists()

    def test_criar_conta_sem_email_e_opcional(self, api_client):
        response = api_client.post(
            "/api/auth/register/",
            {"username": "brunhilda", "password": "SenhaForte123!"},
            format="json",
        )
        assert response.status_code == 201

    def test_username_duplicado_retorna_400(self, api_client, django_user_model):
        django_user_model.objects.create_user(username="kael", password="OutraSenha123!")
        response = api_client.post(
            "/api/auth/register/",
            {"username": "kael", "password": "SenhaForte123!"},
            format="json",
        )
        assert response.status_code == 400

    def test_senha_fraca_retorna_400(self, api_client):
        response = api_client.post(
            "/api/auth/register/",
            {"username": "novo_convocador", "password": "123"},
            format="json",
        )
        assert response.status_code == 400
        assert "password" in response.data

    def test_senha_e_gravada_com_hash_nao_em_texto_plano(self, api_client):
        api_client.post(
            "/api/auth/register/",
            {"username": "sylvanas", "password": "SenhaForte123!"},
            format="json",
        )
        usuario = User.objects.get(username="sylvanas")
        assert usuario.password != "SenhaForte123!"
        assert usuario.check_password("SenhaForte123!")

    def test_conta_criada_permite_login_imediato(self, api_client):
        api_client.post(
            "/api/auth/register/",
            {"username": "thorin", "password": "SenhaForte123!"},
            format="json",
        )
        response = api_client.post(
            "/api/auth/token/",
            {"username": "thorin", "password": "SenhaForte123!"},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data
