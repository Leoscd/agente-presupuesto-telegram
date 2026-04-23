"""Rubro: Losa de hormigón armado.

Fórmulas (dosificación H21):
- m3 = m2 * espesor_cm / 100
- Por m3: 7 bolsas cemento, 0.45 m3 arena, 0.65 m3 piedra
- Hierro 8mm: 1.2 barras por m2
- Plastificante: 1 bidón cada 15 m3
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


class ParamsLosa(BaseModel):
    ancho: PositiveFloat = Field(..., description="Metros")
    largo: PositiveFloat = Field(..., description="Metros")
    espesor_cm: float = Field(12.0, ge=8.0, le=25.0)


def _q(v) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular(params: ParamsLosa, empresa_id: str) -> ResultadoPresupuesto:
    datos = cargar_empresa(empresa_id)
    m2 = params.ancho * params.largo
    m3 = _q(Decimal(str(m2)) * Decimal(str(params.espesor_cm)) / Decimal("100")

    # Materiales por m3 (dosificación H21)
    cant_cemento = ceil(m3 * Decimal("7"))
    cant_arena = _q(m3 * Decimal("0.45"))
    cant_piedra = _q(m3 * Decimal("0.65"))

    # Hierro 8mm: 1.2 barras por m2
    cant_h8 = ceil(m2 * Decimal("1.2"))

    # Plastificante: 1 bidón cada 15 m3
    cant_plastificante = max(1, ceil(m3 / Decimal("15")))

    # Mano de obra
    costo_mo = precio_mano_obra(datos, "LOSA_HORMIGON") * Decimal(str(m2))

    partidas = [
        Partida(concepto="Cemento portland bolsa 50kg", cantidad=cant_cemento, unidad="u", precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"), categoria="material"),
        Partida(concepto="Arena gruesa m3", cantidad=cant_arena, unidad="m3", precio_unitario=precio_material(datos, "ARENA_GRUESA"), categoria="material"),
        Partida(concepto="Piedra partida 6-12mm m3", cantidad=cant_piedra, unidad="m3", precio_unitario=precio_material(datos, "PIEDRA_6_12"), categoria="material"),
        Partida(concepto="Hierro nervado 8mm barra 12m", cantidad=cant_h8, unidad="u", precio_unitario=precio_material(datos, "HIERRO_8"), categoria="material"),
        Partida(concepto="Plastificante Hercal bidon 20L", cantidad=cant_plastificante, unidad="u", precio_unitario=precio_material(datos, "PLASTIFICANTE_HERCAL"), categoria="material"),
        Partida(concepto="Mano de obra losa", cantidad=m2, unidad="m2", precio_unitario=costo_mo / Decimal(str(m2)), categoria="mano_obra"),
    ]

    materiales_faltantes(partidas, datos)

    resultado = ResultadoPresupuesto(
        accion="losa",
        parametros=params.model_dump(),
        partidas=partidas,
        metadata={"superficie_m2": m2, "volumen_m3": float(m3)},
    )

    return resultado


registrar("losa", ParamsLosa, calcular)