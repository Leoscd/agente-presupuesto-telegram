"""Rubro: Revoque grueso interior.

Fórmulas (mortero 1:3 cemento-arena):
- m3_mortero = superficie * espesor_cm / 100
- 1 bolsa cemento (0.035 m3) por cada 0.105 m3 mortero
- Arena: 3 veces el volumen de cemento
- Plastificante: 1 bidón cada 30 m2
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


class ParamsRevoqueGrueso(BaseModel):
    superficie_m2: PositiveFloat = Field(..., description="Metros cuadrados")
    espesor_cm: float = Field(1.5, ge=0.5, le=3.0)


def _q(v) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular(params: ParamsRevoqueGrueso, empresa_id: str) -> ResultadoPresupuesto:
    datos = cargar_empresa(empresa_id)
    m3_mortero = _q(Decimal(str(params.superficie_m2))) * Decimal(str(params.espesor_cm)) / Decimal("100")

    # Cemento: 1 bolsa (0.035 m3) por cada 0.105 m3 mortero
    cant_cemento = ceil(m3_mortero / Decimal("0.035"))
    
    # Arena: 3 veces el volumen de cemento
    cant_arena = _q(m3_mortero * Decimal("3"))
    
    # Plastificante: 1 bidón cada 30 m2
    cant_plastificante = max(1, ceil(Decimal(str(params.superficie_m2)) / Decimal("30")))

    # Mano de obra
    costo_mo = precio_mano_obra(datos, "REVOQUE_GRUESO") * Decimal(str(params.superficie_m2))

    partidas = [
        Partida(concepto="Cemento portland bolsa 50kg", cantidad=cant_cemento, unidad="u", precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"), categoria="material"),
        Partida(concepto="Arena gruesa m3", cantidad=cant_arena, unidad="m3", precio_unitario=precio_material(datos, "ARENA_GRUESA"), categoria="material"),
        Partida(concepto="Plastificante Hercal/Plasticor bidon 20L", cantidad=cant_plastificante, unidad="u", precio_unitario=precio_material(datos, "PLASTIFICANTE_HERCAL"), categoria="material"),
        Partida(concepto="Mano de obra revoque grueso", cantidad=params.superficie_m2, unidad="m2", precio_unitario=costo_mo / Decimal(str(params.superficie_m2)), categoria="mano_obra"),
    ]

    materiales_faltantes(partidas, datos)

    resultado = ResultadoPresupuesto(
        accion="revoque_grueso",
        parametros=params.model_dump(),
        partidas=partidas,
        metadata={"superficie_m2": params.superficie_m2, "volumen_mortero_m3": float(m3_mortero)},
    )

    return resultado


registrar("revoque_grueso", ParamsRevoqueGrueso, calcular)