import logging

import requests

logger = logging.getLogger(__name__)


def fetch_spell_from_dnd_api(spell_index):
    """Busca uma magia na API pública do D&D 5e pelo índice informado."""
    url = f"https://www.dnd5eapi.co/api/spells/{spell_index}"

    try:
        # Timeout curto para evitar bloquear a request em caso de falha de rede.
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            return {
                "nome": data.get("name"),
                "nivel": data.get("level", 0),
                "escola": data.get("school", {}).get("name", "Desconhecida"),
                "descricao": "\n".join(data.get("desc", ["Descrição não disponível."])),
                "fonte_api": spell_index,
            }

        if response.status_code == 404:
            return None

        response.raise_for_status()

    except requests.exceptions.RequestException as exc:
        logger.exception("Falha ao consultar a API do D&D 5e para %s", spell_index)
        raise Exception("Serviço de magias indisponível no momento. Tente mais tarde.") from exc
