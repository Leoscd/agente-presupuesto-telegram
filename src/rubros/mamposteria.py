"""Rubro: Mampostería de ladrillos.

Fórmulas:
- m2 = largo * alto
- ladrillos: cant = ceil(m2 * ladriyos_m2[tipo] * rendimiento(...))
- cemento: 1 bolsa cada 10 m2
- plastificante: 1 bidón cada 25 m2
- arena: 0.03 m3 por m2
- mano de obra: precio_MO * m2
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


class ParamsMamposteria(BaseModel):
    largo: PositiveFloat = Field(..., description="Metros lineales de muro")
    alto: PositiveFloat = Field(..., description="Metros de altura")
    tipo: Literal["hueco_12", "hueco_18", "comun"] = "hueco_12"


CODIGO_LADRILLO = {
    "hueco_12": "LADRILLO_HUECO_12",
    "hueco_18": "LADRILLO_HUECO_18",
    "comun": "LADRILLO_COMUN",
}
CODIGO_TAREA_MO = {
    "hueco_12": "MAMPOSTERIA_HUECO_12",
    "hueco_18": "MAMPOSTERIA_HUECO_18",
    "comun": "MAMPOSTERIA_COMUN",
}
LADRILLOS_POR_M2 = {
    "hueco_12": Decimal("36"),
    "hueco_18": Decimal("28"),
    "comun": Decimal("48"),
}
PLASTIFICANTE_POR_M2 = Decimal("0.04")  # bidones por m2 (1 bidón cada 25m2)


def _q(v) -> Decimal:
    """Redondeo a 2 decimales."""
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular(params: ParamsMamposteria, empresa_id: str) -> ResultadoPresupuesto:
    datos = cargar_empresa(empresa_id)
    m2 = params.largo * params.alto

    cod_ladrillo = CODIGO_LADRILLO[params.tipo]
    cod_mo = CODIGO_TAREA_MO[params.tipo]

    # Ladrillos con rendimiento y 5% desperdicio
    cant_ladrillos = ceil(m2 * LADRILLOS_POR_M2[params.tipo] * rendimiento(datos, cod_ladrillo, Decimal("1.05")))

    # Cemento: 1 bolsa cada 10 m2
    cant_cemento = ceil(m2 / Decimal("10"))

    # Plastificante: 1 bidón cada 25 m2
    cant_plastificante = ceil(m2 * PLASTIFICANTE_POR_M2)

    # Arena: 0.03 m3 por m2
    cant_arena = _q(Decimal(str(m2)) * Decimal("0.03"))

    # Mano de obra
    costo_mo = precio_mano_obra(datos, cod_mo) * Decimal(str(m2))

    partidas = [
        Partida(concepto=f"Ladrillo {params.tipo.replace('_', ' ').title()}", cantidad=cant_ladrillos, unidad="u", precio_unitario=precio_material(datos, cod_ladrillo), categoria="material"),
        Partida(concepto="Cemento portland bolsa 50kg", cantidad=cant_cemento, unidad="u", precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"), categoria="material"),
        Partida(concepto="Plastificante Hercal/Plasticor bidon 20L", cantidad=cant_plastificante, unidad="u", precio_unitario=precio_material(datos, "PLASTIFICANTE_HERCAL"), categoria="material"),
        Partida(concepto="Arena gruesa m3", cantidad=cant_arena, unidad="m3", precio_unitario=precio_material(datos, "ARENA_GRUESA"), categoria="material"),
        Partida(concepto=f"Mano de obra mampostería {params.tipo}", cantidad=m2, unidad="m2", precio_unitario=costo_mo / Decimal(str(m2)), categoria="mano_obra"),
    ]

    # Validar materiales
    materiales_faltantes(partidas, datos)

    resultado = ResultadoPresupuesto(
        accion="mamposteria",
        parametros=params.model_dump(),
        partidas=partidas,
        metadata={"superficie_m2": m2},
    )

    return resultado


registrar("mamposteria", ParamsMamposteria, calcular)