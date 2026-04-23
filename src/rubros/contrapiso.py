"""Rubro: Contrapiso de hormigón.

Fórmulas (hormigón pobre H13):
- m3 = superficie * espesor_cm / 100
- Por m3: 4 bolsas cemento, 0.55 m3 arena, 0.65 m3 piedra
- Mano de obra: precio_MO * m2
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    DatosEmpresa,
    cargar_empresa,
    precio_mano_obra,
    precio_material,
    rendimiento,
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsContrapiso(BaseModel):
    superficie_m2: PositiveFloat = Field(..., description="Metros cuadrados")
    espesor_cm: float = Field(8.0, ge=5.0, le=15.0)


def _q(v) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular(params: ParamsContrapiso, empresa_id: str) -> ResultadoPresupuesto:
    datos = cargar_empresa(empresa_id)
    m3 = _q(Decimal(str(params.superficie_m2))) * Decimal(str(params.espesor_cm)) / Decimal("100")

    # Materiales por m3 (H13)
    cant_cemento = ceil(m3 * Decimal("4"))
    cant_arena = _q(m3 * Decimal("0.55"))
    cant_piedra = _q(m3 * Decimal("0.65"))

    # Mano de obra
    costo_mo = precio_mano_obra(datos, "CONTRAPISO") * Decimal(str(params.superficie_m2))

    partidas = [
        Partida(concepto="Cemento portland bolsa 50kg", cantidad=cant_cemento, unidad="u", precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"), categoria="material"),
        Partida(concepto="Arena gruesa m3", cantidad=cant_arena, unidad="m3", precio_unitario=precio_material(datos, "ARENA_GRUESA"), categoria="material"),
        Partida(concepto="Piedra partida 6-12mm m3", cantidad=cant_piedra, unidad="m3", precio_unitario=precio_material(datos, "PIEDRA_6_12"), categoria="material"),
        Partida(concepto="Mano de obra contrapiso", cantidad=params.superficie_m2, unidad="m2", precio_unitario=costo_mo / Decimal(str(params.superficie_m2)), categoria="mano_obra"),
    ]

    materiales_faltantes(partidas, datos)

    resultado = ResultadoPresupuesto(
        accion="contrapiso",
        parametros=params.model_dump(),
        partidas=partidas,
        metadata={"superficie_m2": params.superficie_m2, "volumen_m3": float(m3)},
    )

    return resultado


registrar("contrapiso", ParamsContrapiso, calcular)