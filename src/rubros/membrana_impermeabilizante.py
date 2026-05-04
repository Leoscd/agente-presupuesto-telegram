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
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsMembrana(BaseModel):
    superficie_m2: PositiveFloat
    tipo: Literal["membrana_asfaltica", "liquida"] = "membrana_asfaltica"
    capas: int = Field(2, ge=1, le=3)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class _CalcMembrana:
    accion = "membrana_impermeabilizante"
    schema_params = ParamsMembrana

    RENDIMIENTO = {  # rollos de 10m2 con 15% solape
        "membrana_asfaltica": Decimal("10"),
    }
    CODIGO_MEMBRANA = {
        "membrana_asfaltica": "MEMBRANA_ASFALTICA",
        "liquida": "MEMBRANA_LIQUIDA",
    }

    def calcular(self, params: ParamsMembrana, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        cod_mat = _CalcMembrana.CODIGO_MEMBRANA[params.tipo]
        faltantes = materiales_faltantes(datos, [cod_mat])
        if faltantes:
            raise ValueError(
                f"Materiales no disponibles en {empresa_id}: {', '.join(faltantes)}"
            )

        sup = Decimal(str(params.superficie_m2))

        if params.tipo == "membrana_asfaltica":
            # 1 rollo cubre 10m2, solapar 15%
            cant_material = Decimal(
                ceil(
                    float(sup * Decimal("1.15") / _CalcMembrana.RENDIMIENTO["membrana_asfaltica"])
                )
            ) * Decimal(str(params.capas))
            concepto = "Membrana asfaltica rollo 10m2"
        elif params.tipo == "liquida":
            # 1 kg por m2 por capa; balde 20kg
            cant_material = Decimal(
                ceil(float(sup * Decimal(str(params.capas))) / 20.0)
            )
            concepto = "Membrana liquida balde 20kg"

        # Mano de obra
        p_mo = precio_mano_obra(datos, "MEMBRANA_IMPERMEAB")
        p_mat = precio_material(datos, cod_mat)

        sub_mat_val = _q(cant_material * p_mat)
        sub_mo_val = _q(p_mo * sup)

        # Partidas
        partidas = [
            Partida(
                concepto=concepto,
                cantidad=cant_material,
                unidad="u",
                precio_unitario=p_mat,
                subtotal=sub_mat_val,
                categoria="material",
            ),
            Partida(
                concepto="MO impermeabilizacion",
                cantidad=sup,
                unidad="m2",
                precio_unitario=p_mo,
                subtotal=sub_mo_val,
                categoria="mano_obra",
            ),
        ]

        total = _q(sub_mat_val + sub_mo_val)

        metadata = {
            "superficie_m2": params.superficie_m2,
            "tipo": params.tipo,
            "capas": params.capas,
            "cant_material": float(cant_material),
        }

        return ResultadoPresupuesto(
            rubro="membrana_impermeabilizante",
            partidas=partidas,
            subtotal_materiales=sub_mat_val,
            subtotal_mano_obra=sub_mo_val,
            total=total,
            metadata=metadata,
            advertencias=[],
        )


registrar(_CalcMembrana())