"""Rubro: Contrapiso de hormigón."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
)
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsContrapiso(BaseModel):
    superficie_m2: PositiveFloat = Field(..., description="Metros cuadrados")
    espesor_cm: float = Field(8.0, ge=5.0, le=15.0)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcContrapiso:
    accion = "contrapiso"
    schema_params = ParamsContrapiso

    @staticmethod
    def calcular(params: ParamsContrapiso, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        m3 = _q(Decimal(str(params.superficie_m2))) * Decimal(str(params.espesor_cm)) / Decimal("100")

        cant_cemento = ceil(m3 * Decimal("4"))
        cant_arena = _q(m3 * Decimal("0.55"))
        cant_piedra = _q(m3 * Decimal("0.65"))
        costo_mo = precio_mano_obra(datos, "CONTRAPISO") * Decimal(str(params.superficie_m2))

        partidas = [
            Partida(concepto="Cemento portland", cantidad=cant_cemento, unidad="u", precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"), subtotal=cant_cemento * precio_material(datos, "CEMENTO_PORTLAND"), categoria="material"),
            Partida(concepto="Arena gruesa", cantidad=cant_arena, unidad="m3", precio_unitario=precio_material(datos, "ARENA_GRUESA"), subtotal=cant_arena * precio_material(datos, "ARENA_GRUESA"), categoria="material"),
            Partida(concepto="Piedra partida", cantidad=cant_piedra, unidad="m3", precio_unitario=precio_material(datos, "PIEDRA_6_12"), subtotal=cant_piedra * precio_material(datos, "PIEDRA_6_12"), categoria="material"),
            Partida(concepto="MO contrapiso", cantidad=Decimal(str(params.superficie_m2)), unidad="m2", precio_unitario=precio_mano_obra(datos, "CONTRAPISO"), subtotal=costo_mo, categoria="mano_obra"),
        ]

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        return ResultadoPresupuesto(
            rubro="contrapiso",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={"superficie_m2": params.superficie_m2, "volumen_m3": float(m3)},
        )


registrar(CalcContrapiso())
