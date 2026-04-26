"""Rubro: impermeabilización con membrana asfáltica o líquida."""
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
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsMembrana(BaseModel):
    superficie_m2: PositiveFloat
    tipo: Literal["asfaltica", "liquida"] = "asfaltica"
    capas: int = Field(2, ge=1, le=3)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcMembrana:
    """Calculadora de impermeabilización con membrana."""

    RENDIMIENTO = {  # m2 por unidad
        "asfaltica": Decimal("10"),
        "liquida": Decimal("20"),
    }
    CODIGO_MEMBRANA = {
        "asfaltica": "MEMBRANA_ASFALTICA",
        "liquida": "MEMBRANA_LIQUIDA",
    }

    def __init__(self, datos: DatosEmpresa):
        self.datos = datos

    def calcular(self, params: ParamsMembrana) -> ResultadoPresupuesto:
        sup = Decimal(str(params.superficie_m2))

        # Determinar código de membrana según tipo
        if params.tipo == "asfaltica":
            # 1 rollo cubre 10m2, solapar 15%
            cant_rollos = Decimal(
                ceil(
                    float(sup * Decimal("1.15") / self.RENDIMIENTO["asfaltica"])
                )
            ) * Decimal(str(params.capas))
            cod_mat = self.CODIGO_MEMBRANA["asfaltica"]
            concep = "Membrana asfáltica rollo 10m2"
            cant_material = cant_rollos

        else:  # liquida
            # 1 kg por m2 por capa; balde 20kg
            cant_baldes = Decimal(
                ceil(float(sup * Decimal(str(params.capas))) / 20.0)
            )
            cod_mat = self.CODIGO_MEMBRANA["liquida"]
            concep = "Membrana líquida balde 20kg"
            cant_material = cant_baldes

        # Material: membrana
        partidas = [
            Partida(
                codigo=cod_mat,
                concepto=concep,
                cantidad=cant_material,
                unidad="u",
            )
        ]

        # Mano de obra
        p_mo = precio_mano_obra(self.datos, "MEMBRANA_IMPERMEAB")
        costo_mo = _q(p_mo * sup)

        partidas.append(
            Partida(
                codigo="",
                concepto="MO impermeabilización",
                cantidad=sup,
                unidad="m2",
                precio_unitario=p_mo,
                subtotal=costo_mo,
            )
        )

        # Validar materiales
        materiales_faltantes([cod_mat])

        # Calcular totals
        subtotal_material = _q(precio_material(self.datos, cod_mat) * cant_material)
        total = _q(subtotal_material + costo_mo)

        metadata = {
            "superficie_m2": params.superficie_m2,
            "tipo": params.tipo,
            "capas": params.capas,
            "cant_material": float(cant_material),
        }

        return ResultadoPresupuesto(
            partidas=partidas,
            subtotal=subtotal_material,
            total=total,
            metadata=metadata,
            advertencias=[],
        )


def registrar_calc():
    """Registrar esta calculadora."""
    from src.rubros.base import ResultadoRubro

    return ResultadoRubro(
        nombre="membrana_impermeabilizante",
        cls=CalcMembrana,
    )