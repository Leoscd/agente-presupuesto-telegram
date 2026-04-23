"""Rubro: Losa de hormigón armado."""
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


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcLosa:
    accion = "losa"
    schema_params = ParamsLosa

    @staticmethod
    def calcular(params: ParamsLosa, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        m2 = params.ancho * params.largo
        m3 = _q(Decimal(str(m2))) * Decimal(str(params.espesor_cm)) / Decimal("100")

        cant_cemento = ceil(m3 * Decimal("7"))
        cant_arena = _q(m3 * Decimal("0.45"))
        cant_piedra = _q(m3 * Decimal("0.65"))
        cant_h8 = ceil(m2 * Decimal("1.2"))
        cant_plast = max(1, ceil(m3 / Decimal("15")))
        costo_mo = precio_mano_obra(datos, "LOSA_HORMIGON") * Decimal(str(m2))

        partidas = [
            Partida(concepto="Cemento portland", cantidad=cant_cemento, unidad="u", precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"), subtotal=cant_cemento * precio_material(datos, "CEMENTO_PORTLAND"), categoria="material"),
            Partida(concepto="Arena gruesa", cantidad=cant_arena, unidad="m3", precio_unitario=precio_material(datos, "ARENA_GRUESA"), subtotal=cant_arena * precio_material(datos, "ARENA_GRUESA"), categoria="material"),
            Partida(concepto="Piedra partida", cantidad=cant_piedra, unidad="m3", precio_unitario=precio_material(datos, "PIEDRA_6_12"), subtotal=cant_piedra * precio_material(datos, "PIEDRA_6_12"), categoria="material"),
            Partida(concepto="Hierro 8mm", cantidad=cant_h8, unidad="u", precio_unitario=precio_material(datos, "HIERRO_8"), subtotal=cant_h8 * precio_material(datos, "HIERRO_8"), categoria="material"),
            Partida(concepto="Plastificante Hercal", cantidad=cant_plast, unidad="u", precio_unitario=precio_material(datos, "PLASTIFICANTE_HERCAL"), subtotal=cant_plast * precio_material(datos, "PLASTIFICANTE_HERCAL"), categoria="material"),
            Partida(concepto="MO losa", cantidad=m2, unidad="m2", precio_unitario=costo_mo / Decimal(str(m2)), subtotal=costo_mo, categoria="mano_obra"),
        ]

        materiales_faltantes(partidas, datos)

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        return ResultadoPresupuesto(
            rubro="losa",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={"superficie_m2": m2, "volumen_m3": float(m3)},
        )


registrar(CalcLosa())