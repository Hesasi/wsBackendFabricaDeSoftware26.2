"""
Testes da camada de serviço (core/services.py).

Cobre os três caminhos descritos na Seção 5.1 do ADR:
sucesso (200), magia inexistente (404) e falha de rede/timeout.
A chamada HTTP real nunca é feita — é sempre mockada.
"""
from unittest.mock import Mock, patch

import pytest
import requests

from core.services import fetch_spell_from_dnd_api


class TestFetchSpellFromDndApi:
    @patch("core.services.requests.get")
    def test_sucesso_retorna_dados_normalizados(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Fireball",
            "level": 3,
            "school": {"name": "Evocation"},
            "desc": ["Uma explosão de fogo.", "Causa dano em área."],
        }
        mock_get.return_value = mock_response

        resultado = fetch_spell_from_dnd_api("fireball")

        assert resultado["nome"] == "Fireball"
        assert resultado["nivel"] == 3
        assert resultado["escola"] == "Evocation"
        assert "explosão de fogo" in resultado["descricao"]
        assert resultado["fonte_api"] == "fireball"
        mock_get.assert_called_once_with(
            "https://www.dnd5eapi.co/api/spells/fireball", timeout=5
        )

    @patch("core.services.requests.get")
    def test_campos_de_conjuracao_ausentes_na_api_retornam_none(self, mock_get):
        """Magias sem casting_time/range/etc. (dict mínimo) não devem quebrar o parsing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Fireball",
            "level": 3,
            "school": {"name": "Evocation"},
            "desc": ["Uma explosão de fogo."],
        }
        mock_get.return_value = mock_response

        resultado = fetch_spell_from_dnd_api("fireball")

        assert resultado["tempo_conjuracao"] is None
        assert resultado["alcance"] is None
        assert resultado["componentes"] is None
        assert resultado["material"] is None
        assert resultado["duracao"] is None
        assert resultado["ritual"] is False
        assert resultado["concentracao"] is False
        assert resultado["dano"] is None
        assert resultado["cd"] is None
        assert resultado["area_efeito"] is None

    @patch("core.services.requests.get")
    def test_campos_de_conjuracao_completos_sao_normalizados(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Fireball",
            "level": 3,
            "school": {"name": "Evocation"},
            "desc": ["Uma explosão de fogo."],
            "casting_time": "1 action",
            "range": "150 feet",
            "components": ["V", "S", "M"],
            "material": "A tiny ball of bat guano and sulfur.",
            "duration": "Instantaneous",
            "ritual": False,
            "concentration": False,
            "damage": {
                "damage_type": {"name": "Fire"},
                "damage_at_slot_level": {"3": "8d6", "4": "9d6"},
            },
            "dc": {"dc_type": {"name": "Dexterity"}, "dc_success": "half"},
            "area_of_effect": {"type": "sphere", "size": 20},
        }
        mock_get.return_value = mock_response

        resultado = fetch_spell_from_dnd_api("fireball")

        assert resultado["tempo_conjuracao"] == "1 action"
        assert resultado["alcance"] == "150 feet"
        assert resultado["componentes"] == "V, S, M"
        assert resultado["material"] == "A tiny ball of bat guano and sulfur."
        assert resultado["duracao"] == "Instantaneous"
        assert resultado["ritual"] is False
        assert resultado["concentracao"] is False
        assert resultado["dano"] == "8d6 de dano de Fire"
        assert resultado["cd"] == "Dexterity (metade do dano no sucesso)"
        assert resultado["area_efeito"] == "20 ft (sphere)"

    @patch("core.services.requests.get")
    def test_magia_inexistente_retorna_none(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        resultado = fetch_spell_from_dnd_api("magia-que-nao-existe")

        assert resultado is None

    @patch("core.services.requests.get")
    def test_falha_de_rede_levanta_excecao_de_dominio(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Falha de rede")

        with pytest.raises(Exception) as exc_info:
            fetch_spell_from_dnd_api("fireball")

        assert "indisponível" in str(exc_info.value)

    @patch("core.services.requests.get")
    def test_timeout_levanta_excecao_de_dominio(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Tempo esgotado")

        with pytest.raises(Exception) as exc_info:
            fetch_spell_from_dnd_api("fireball")

        assert "indisponível" in str(exc_info.value)

    @patch("core.services.requests.get")
    def test_erro_5xx_da_api_externa_levanta_excecao_de_dominio(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "500 Server Error"
        )
        mock_get.return_value = mock_response

        with pytest.raises(Exception):
            fetch_spell_from_dnd_api("fireball")
