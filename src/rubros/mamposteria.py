"""Rubro: Mampostería de ladrillos."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
    rendimiento,
)
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
PLASTIFICANTE_POR_M2 = Decimal("0.04")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcMamposteria:
    accion = "mamposteria"
    schema_params = ParamsMamposteria

    @staticmethod
    def calcular(params: ParamsMamposteria, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        m2 = Decimal(str(params.largo * params.alto))

        cod_ladrillo = CODIGO_LADRILLO[params.tipo]
        cod_mo = CODIGO_TAREA_MO[params.tipo]

        m2d = Decimal(str(m2))
        cant_ladrillos = Decimal(ceil(m2d * LADRILLOS_POR_M2[params.tipo] * rendimiento(datos, cod_ladrillo, Decimal("1.05"))))
        cant_cemento = Decimal(ceil(m2d / Decimal("10")))
        cant_plastificante = Decimal(ceil(m2d * PLASTIFICANTE_POR_M2))
        cant_arena = _q(m2d * Decimal("0.03"))
        costo_mo = precio_mano_obra(datos, cod_mo) * m2d

        partidas = [
            Partida(concepto=f"Ladrillo {params.tipo}", cantidad=cant_ladrillos, unidad="u", precio_unitario=precio_material(datos, cod_ladrillo), subtotal=cant_ladrillos * precio_material(datos, cod_ladrillo), categoria="material"),
            Partida(concepto="Cemento portland", cantidad=cant_cemento, unidad="u", precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"), subtotal=cant_cemento * precio_material(datos, "CEMENTO_PORTLAND"), categoria="material"),
            Partida(concepto="Plastificante Hercal", cantidad=cant_plastificante, unidad="u", precio_unitario=precio_material(datos, "PLASTIFICANTE_HERCAL"), subtotal=cant_plastificante * precio_material(datos, "PLASTIFICANTE_HERCAL"), categoria="material"),
            Partida(concepto="Arena gruesa", cantidad=cant_arena, unidad="m3", precio_unitario=precio_material(datos, "ARENA_GRUESA"), subtotal=cant_arena * precio_material(datos, "ARENA_GRUESA"), categoria="material"),
            Partida(concepto="MO mampostería", cantidad=m2d, unidad="m2", precio_unitario=precio_mano_obra(datos, cod_mo), subtotal=costo_mo, categoria="mano_obra"),
        ]

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        return ResultadoPresupuesto(
            rubro="mamposteria",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={"superficie_m2": float(m2d)},
        )


registrar(CalcMamposteria())