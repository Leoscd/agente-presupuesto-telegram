"""Cliente MiniMax-M2 con JSON mode, retry y token accounting.

MiniMax expone un endpoint OpenAI-compatible, así que usamos la SDK oficial de OpenAI apuntando a MINIMAX_BASE_URL.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from src.config import settings
from src.orquestador.prompts import SYSTEM_PROMPT, SYSTEM_PROMPT_CATEGORIA, build_user_message
from src.persistencia import db

log = logging.getLogger(__name__)

# Pricing asumido MiniMax-M2 (USD por 1M tokens). Verificar al hacer deploy.
USD_PER_1M_INPUT = 0.30
USD_PER_1M_OUTPUT = 1.20


@dataclass
class RespuestaOrq:
    accion: str
    parametros: dict
    confianza: float
    raw: dict
    tokens_input: int
    tokens_output: int
    usd_estimado: float
    latencia_ms: int


_client: AsyncOpenAI | None = None


def _cliente() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.minimax_api_key,
            base_url=settings.minimax_base_url,
            timeout=30.0,
        )
    return _client


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _strip_think(content: str) -> str:
    """MiniMax-M2 outputs <think>...</think> before JSON, sometimes wrapped in markdown fences.
    Strips both; falls back to regex extraction if think block is truncated.
    """
    clean = _THINK_RE.sub("", content).strip()
    # strip markdown code fences if present
    fence_m = _FENCE_RE.search(clean)
    if fence_m:
        clean = fence_m.group(1).strip()
    if clean:
        return clean
    # think block truncated — extract first {...} directly
    m = _JSON_RE.search(content)
    return m.group(0) if m else "{}"


def _estimar_usd(tin: int, tout: int) -> float:
    return round(tin / 1_000_000 * USD_PER_1M_INPUT + tout / 1_000_000 * USD_PER_1M_OUTPUT, 6)


async def clasificar_categoria(texto: str) -> tuple[str, float]:
    """Clasifica el pedido en una categoría para filtrar acciones."""
    t0 = time.perf_counter()
    try:
        resp: ChatCompletion = await _cliente().chat.completions.create(
            model=settings.minimax_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_CATEGORIA},
                {"role": "user", "content": texto},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000,
        )
        latencia_ms = int((time.perf_counter() - t0) * 1000)
        content = _strip_think(resp.choices[0].message.content or "{}")
        raw = json.loads(content)
        categoria = str(raw.get("categoria", ""))
        confianza = float(raw.get("confianza", 0.0))
        return categoria, confianza
    except Exception as e:
        log.warning("Error clasificando categoría: %s", e)
        return "", 0.0


async def parsear(texto_usuario: str, materiales_disponibles: list[str], acciones_filtradas: list[str] | None = None) -> RespuestaOrq:
    t0 = time.perf_counter()
    user_msg = build_user_message(texto_usuario, materiales_disponibles, acciones_filtradas)

    resp: ChatCompletion = await _cliente().chat.completions.create(
        model=settings.minimax_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1000,
    )

    latencia_ms = int((time.perf_counter() - t0) * 1000)
    content = _strip_think(resp.choices[0].message.content or "{}")
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as e:
        log.warning("MiniMax devolvió JSON inválido: %s — payload: %s", e, content)
        raw = {"accion": "aclaracion", "parametros": {"pregunta": "¿Podés reformular el pedido?"}, "confianza": 0.0}

    usage = resp.usage
    tin = usage.prompt_tokens if usage else 0
    tout = usage.completion_tokens if usage else 0
    usd = _estimar_usd(tin, tout)

    db.acumular_tokens(tin, tout, usd)

    return RespuestaOrq(
        accion=str(raw.get("accion", "")),
        parametros=dict(raw.get("parametros", {})),
        confianza=float(raw.get("confianza", 0.0)),
        raw=raw,
        tokens_input=tin,
        tokens_output=tout,
        usd_estimado=usd,
        latencia_ms=latencia_ms,
    )
