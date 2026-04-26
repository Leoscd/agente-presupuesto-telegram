"""Rubro: estructura metálica con perfil IPN."""
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


class ParamsEstructuraMetalica(BaseModel):
    longitud_ml: PositiveFloat
    tipo_perfil: Literal["IPN_120", "IPN_140", "IPN_160"] = "IPN_120"
    proteccion: bool = Field(True, description="Incluye pintura anticorrosiva")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcEstructuraMetalica:
    """Calculadora de estructura metálica."""

    CODIGO_PERFIL = {
        "IPN_120": "PERFIL_IPN_120",
        "IPN_140": "PERFIL_IPN_120",  # por ahora mismo
        "IPN_160": "PERFIL_IPN_120",
    }
    PESO_KG_ML = {  # kg por ml de perfil
        "IPN_120": Decimal("13.0"),
        "IPN_140": Decimal("16.0"),
        "IPN_160": Decimal("19.0"),
    }

    def __init__(self, datos: DatosEmpresa):
        self.datos = datos

    def calcular(self, params: ParamsEstructuraMetalica) -> ResultadoPresupuesto:
        long = Decimal(str(params.longitud_ml))

        # Perfil: barras de 12m
        cant_barras = Decimal(ceil(float(long) / 12.0))
        cod_perfil = self.CODIGO_PERFIL[params.tipo_perfil]

        partidas = [
            Partida(
                codigo=cod_perfil,
                concepto=f"Perfil {params.tipo_perfil} barra 12m",
                cantidad=cant_barras,
                unidad="u",
            )
        ]

        # Peso del perfil para electrodos
        peso_total = long * self.PESO_KG_ML[params.tipo_perfil]

        # Pintura anticorrosiva si aplica
        cant_latas = Decimal(0)
        if params.proteccion:
            # 0.45 m2/ml de perfil, rendimiento 10 m2/L, lata 4L
            m2_perfil = _q(long * Decimal("0.45"))
            litros_ant = m2_perfil / Decimal("10")
            cant_latas = Decimal(ceil(float(litros_ant) / 4.0))

            partidas.append(
                Partida(
                    codigo="PINTURA_ANTICORR",
                    concepto="Pintura anticorrosiva lata 4L",
                    cantidad=cant_latas,
                    unidad="u",
                )
            )

        # Electrodos: ~1 caja por cada 200kg de estructura
        cant_cajas_elec = Decimal(ceil(float(peso_total) / 200))

        partidas.append(
            Partida(
                codigo="ELECTRODO_E6013",
                concepto="Electrodos E6013 caja 50u",
                cantidad=cant_cajas_elec,
                unidad="u",
            )
        )

        # Mano de obra
        p_mo = precio_mano_obra(self.datos, "ESTRUCTURA_METALICA")
        costo_mo = _q(p_mo * long)

        partidas.append(
            Partida(
                codigo="",
                concepto="MO estructura metálica",
                cantidad=long,
                unidad="ml",
                precio_unitario=p_mo,
                subtotal=costo_mo,
            )
        )

        # Validar materiales
        materiales_faltantes(
            [cod_perfil, "PINTURA_ANTICORR", "ELECTRODO_E6013"]
        )

        # Calcular totals
        subtotal_material = _q(
            precio_material(self.datos, cod_perfil) * cant_barras
            + precio_material(self.datos, "PINTURA_ANTICORR") * cant_latas
            + precio_material(self.datos, "ELECTRODO_E6013") * cant_cajas_elec
        )
        total = _q(subtotal_material + costo_mo)

        metadata = {
            "longitud_ml": params.longitud_ml,
            "tipo_perfil": params.tipo_perfil,
            "proteccion": params.proteccion,
            "cant_barras": float(cant_barras),
            "peso_total_kg": float(peso_total),
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
        nombre="estructura_metalica",
        cls=CalcEstructuraMetalica,
    )