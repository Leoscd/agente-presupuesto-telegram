"""Rubro: impermeabilización con membrana asfáltica o líquida."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Literal

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
)
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsMembrana(BaseModel):
    superficie_m2: PositiveFloat
    tipo: Literal["asfaltica", "liquida"] = "asfaltica"
    capas: int = Field(2, ge=1, le=3)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcMembrana:
    accion = "membrana_impermeabilizante"
    schema_params = ParamsMembrana

    RENDIMIENTO = {  # m2 por unidad
        "asfaltica": Decimal("10"),
        "liquida": Decimal("20"),
    }
    CODIGO_MEMBRANA = {
        "asfaltica": "MEMBRANA_ASFALTICA",
        "liquida": "MEMBRANA_LIQUIDA",
    }

    @staticmethod
    def calcular(params: ParamsMembrana, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        sup = Decimal(str(params.superficie_m2))

        # Material: membrana según tipo
        cod_mat = CalcMembrana.CODIGO_MEMBRANA[params.tipo]

        if params.tipo == "asfaltica":
            # 1 rollo cubre 10m2, solapar 15%
            cant_material = Decimal(
                ceil(
                    float(sup * Decimal("1.15") / CalcMembrana.RENDIMIENTO["asfaltica"])
                )
            ) * Decimal(str(params.capas))
            concepto = "Membrana asfáltica rollo 10m2"
            cant_material = Decimal(ceil(Decimal(str(params.capas)) * sup / Decimal("20")))

        # Mano de obra
        p_mo = precio_mano_obra(datos, "MEMBRANA_IMPERMEAB")
        costo_mo = _q(p_mo * sup)

        # Partidas
        partidas = [
            Partida(
                concepto=concepto,
                cantidad=cant_material,
                unidad="u",
                precio_unitario=precio_material(datos, cod_mat),
                subtotal=_q(cant_material * precio_material(datos, cod_mat)),
                categoria="material",
            ),
            Partida(
                concepto="MO impermeabilización",
                cantidad=sup,
                unidad="m2",
                precio_unitario=p_mo,
                subtotal=costo_mo,
                categoria="mano_obra",
            ),
        ]

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum(
            (p.subtotal for p in partidas if p.categoria == "material"),
            Decimal("0"),
        )
        sub_mo = sum(
            (p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0")
        )

        metadata = {
            "superficie_m2": params.superficie_m2,
            "tipo": params.tipo,
            "capas": params.capas,
            "cant_material": float(cant_material),
        }

        return ResultadoPresupuesto(
            rubro="membrana_impermeabilizante",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata=metadata,
            advertencias=[],
        )


registrar(CalcMembrana())