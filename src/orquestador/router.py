"""Dispatch del JSON parseado a la calculadora correspondiente."""
from __future__ import annotations

from pydantic import ValidationError

from src.rubros import REGISTRY
from src.rubros.base import ResultadoPresupuesto
from src.rubros.categorias import CATEGORIAS


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


async def despachar_con_pipeline(
    texto: str, empresa_id: str, materiales_disponibles: list[str]
) -> tuple[ResultadoPresupuesto | None, "RespuestaOrq"]:
    """Two-stage: clasificar categoría → parsear acción filtrada → calcular."""
    from src.orquestador.minimax_client import clasificar_categoria, parsear

    cat, conf_cat = await clasificar_categoria(texto)
    if cat and conf_cat >= 0.8:
        acciones = CATEGORIAS.get(cat, [])
    else:
        acciones = None  # sin filtro

    resp = await parsear(texto, materiales_disponibles, acciones_filtradas=acciones)
    if resp.accion == "aclaracion":
        # No calcular, retornar para que el handler pregunte
        return None, resp
    resultado = despachar(resp.accion, resp.parametros, empresa_id)
    return resultado, resp
