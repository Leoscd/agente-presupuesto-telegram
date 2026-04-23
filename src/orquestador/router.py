"""Dispatch del JSON parseado a la calculadora correspondiente."""
from __future__ import annotations

from pydantic import ValidationError

from src.rubros import REGISTRY
from src.rubros.base import ResultadoPresupuesto


class AccionDesconocida(Exception):
    pass


def despachar(accion: str, parametros: dict, empresa_id: str) -> ResultadoPresupuesto:
    calc = REGISTRY.get(accion)
    if calc is None:
        raise AccionDesconocida(f"No hay calculadora para la acción '{accion}'")
    try:
        params = calc.schema_params(**parametros)
    except ValidationError as e:
        raise ValueError(f"Parámetros inválidos para {accion}: {e}") from e
    return calc.calcular(params, empresa_id)
