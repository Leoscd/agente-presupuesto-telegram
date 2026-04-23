"""Rubro: Revoque grueso interior."""
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


class ParamsRevoqueGrueso(BaseModel):
    superficie_m2: PositiveFloat = Field(..., description="Metros cuadrados")
    espesor_cm: float = Field(1.5, ge=0.5, le=3.0)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcRevoqueGrueso:
    accion = "revoque_grueso"
    schema_params = ParamsRevoqueGrueso

    @staticmethod
    def calcular(params: ParamsRevoqueGrueso, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        m3_mortero = _q(Decimal(str(params.superficie_m2))) * Decimal(str(params.espesor_cm)) / Decimal("100")

        supm2 = Decimal(str(params.superficie_m2))
        cant_cemento = Decimal(ceil(m3_mortero / Decimal("0.035")))
        cant_arena = _q(m3_mortero * Decimal("3"))
        cant_plast = Decimal(max(1, ceil(supm2 / Decimal("30"))))
        p_mo = precio_mano_obra(datos, "REVOQUE_GRUESO")
        costo_mo = p_mo * supm2

        partidas = [
            Partida(concepto="Cemento portland", cantidad=cant_cemento, unidad="u", precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"), subtotal=cant_cemento * precio_material(datos, "CEMENTO_PORTLAND"), categoria="material"),
            Partida(concepto="Arena gruesa", cantidad=cant_arena, unidad="m3", precio_unitario=precio_material(datos, "ARENA_GRUESA"), subtotal=cant_arena * precio_material(datos, "ARENA_GRUESA"), categoria="material"),
            Partida(concepto="Plastificante Hercal", cantidad=cant_plast, unidad="u", precio_unitario=precio_material(datos, "PLASTIFICANTE_HERCAL"), subtotal=cant_plast * precio_material(datos, "PLASTIFICANTE_HERCAL"), categoria="material"),
            Partida(concepto="MO revoque grueso", cantidad=supm2, unidad="m2", precio_unitario=p_mo, subtotal=costo_mo, categoria="mano_obra"),
        ]

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        return ResultadoPresupuesto(
            rubro="revoque_grueso",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={"superficie_m2": params.superficie_m2, "volumen_mortero_m3": float(m3_mortero)},
        )


registrar(CalcRevoqueGrueso())
