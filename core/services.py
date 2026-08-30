import logging

import requests

logger = logging.getLogger(__name__)


def _formatar_componentes(data):
    componentes = data.get("components") or []
    return ", ".join(componentes) if componentes else None


def _formatar_dano(data):
    """Resume o bloco 'damage' da API em uma string curta, ex: '8d6 de dano de Fogo'."""
    damage = data.get("damage")
    if not damage:
        return None

    tipo = (damage.get("damage_type") or {}).get("name")
    tabela_dano = damage.get("damage_at_slot_level") or damage.get("damage_at_character_level") or {}
    dado = None
    if tabela_dano:
        try:
            primeira_chave = sorted(tabela_dano.keys(), key=lambda k: int(k))[0]
        except (ValueError, TypeError):
            primeira_chave = next(iter(tabela_dano))
        dado = tabela_dano.get(primeira_chave)

    if dado and tipo:
        return f"{dado} de dano de {tipo}"
    return dado or tipo


def _formatar_cd(data):
    """Resume o bloco 'dc' (saving throw) da API, ex: 'Constituição (metade do dano no sucesso)'."""
    dc = data.get("dc")
    if not dc:
        return None

    tipo = (dc.get("dc_type") or {}).get("name")
    sucesso = {"half": "metade do dano no sucesso", "none": "sem efeito no sucesso"}.get(
        dc.get("dc_success"), dc.get("dc_success")
    )
    partes = [p for p in [tipo, sucesso] if p]
    if len(partes) == 2:
        return f"{partes[0]} ({partes[1]})"
    return partes[0] if partes else None


def _formatar_area_efeito(data):
    area = data.get("area_of_effect")
    if not area:
        return None
    tipo = area.get("type")
    tamanho = area.get("size")
    if tipo and tamanho:
        return f"{tamanho} ft ({tipo})"
    return tipo


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
                # Detalhes de conjuração — todos opcionais, nem toda magia os possui.
                "tempo_conjuracao": data.get("casting_time"),
                "alcance": data.get("range"),
                "componentes": _formatar_componentes(data),
                "material": data.get("material"),
                "duracao": data.get("duration"),
                "ritual": bool(data.get("ritual", False)),
                "concentracao": bool(data.get("concentration", False)),
                "dano": _formatar_dano(data),
                "cd": _formatar_cd(data),
                "area_efeito": _formatar_area_efeito(data),
            }

        if response.status_code == 404:
            return None

        response.raise_for_status()

    except requests.exceptions.RequestException as exc:
        logger.exception("Falha ao consultar a API do D&D 5e para %s", spell_index)
        raise Exception("Serviço de magias indisponível no momento. Tente mais tarde.") from exc
