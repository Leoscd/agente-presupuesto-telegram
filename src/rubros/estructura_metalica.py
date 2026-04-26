"""Rubro: estructura metálica con perfil IPN."""
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


class ParamsEstructuraMetalica(BaseModel):
    longitud_ml: PositiveFloat
    tipo_perfil: Literal["IPN_120", "IPN_140", "IPN_160"] = "IPN_120"
    proteccion: bool = Field(True, description="Incluye pintura anticorrosiva")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcEstructuraMetalica:
    accion = "estructura_metalica"
    schema_params = ParamsEstructuraMetalica

    CODIGO_PERFIL = {
        "IPN_120": "PERFIL_IPN_120",
        "IPN_140": "PERFIL_IPN_120",  # por ahora mismo código
        "IPN_160": "PERFIL_IPN_120",
    }
    PESO_KG_ML = {  # kg por ml de perfil
        "IPN_120": Decimal("13.0"),
        "IPN_140": Decimal("16.0"),
        "IPN_160": Decimal("19.0"),
    }

    @staticmethod
    def calcular(params: ParamsEstructuraMetalica, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)
        long = Decimal(str(params.longitud_ml))

        # Perfil: barras de 12m
        cant_barras = Decimal(ceil(float(long) / 12.0))
        cod_perfil = CalcEstructuraMetalica.CODIGO_PERFIL[params.tipo_perfil]

        # Peso del perfil para electrodos
        peso_total = long * CalcEstructuraMetalica.PESO_KG_ML[params.tipo_perfil]

        # Partidas
        partidas = [
            Partida(
                concepto=f"Perfil {params.tipo_perfil} barra 12m",
                cantidad=cant_barras,
                unidad="u",
                precio_unitario=precio_material(datos, cod_perfil),
                subtotal=_q(cant_barras * precio_material(datos, cod_perfil)),
                categoria="material",
            )
        ]

        # Pintura anticorrosiva si aplica
        cant_latas = Decimal(0)
        if params.proteccion:
            # 0.45 m2/ml de perfil, rendimiento 10 m2/L, lata 4L
            m2_perfil = _q(long * Decimal("0.45"))
            litros_ant = m2_perfil / Decimal("10")
            cant_latas = Decimal(ceil(float(litros_ant) / 4.0))

            partidas.append(
                Partida(
                    concepto="Pintura anticorrosiva lata 4L",
                    cantidad=cant_latas,
                    unidad="u",
                    precio_unitario=precio_material(datos, "PINTURA_ANTICORR"),
                    subtotal=_q(cant_latas * precio_material(datos, "PINTURA_ANTICORR")),
                    categoria="material",
                )
            )

        # Electrodos: ~1 caja por cada 200kg de estructura
        cant_cajas_elec = Decimal(ceil(float(peso_total) / 200))

        partidas.append(
            Partida(
                concepto="Electrodos E6013 caja 50u",
                cantidad=cant_cajas_elec,
                unidad="u",
                precio_unitario=precio_material(datos, "ELECTRODO_E6013"),
                subtotal=_q(cant_cajas_elec * precio_material(datos, "ELECTRODO_E6013")),
                categoria="material",
            )
        )

        # Mano de obra
        p_mo = precio_mano_obra(datos, "ESTRUCTURA_METALICA")
        costo_mo = _q(p_mo * long)

        partidas.append(
            Partida(
                concepto="MO estructura metálica",
                cantidad=long,
                unidad="ml",
                precio_unitario=p_mo,
                subtotal=costo_mo,
                categoria="mano_obra",
            )
        )

        # Totals
        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum(
            (p.subtotal for p in partidas if p.categoria == "material"),
            Decimal("0"),
        )
        sub_mo = sum(
            (p.subtotal for p in partidas if p.categoria == "mano_obra"),
            Decimal("0"),
        )

        metadata = {
            "longitud_ml": params.longitud_ml,
            "tipo_perfil": params.tipo_perfil,
            "proteccion": params.proteccion,
            "cant_barras": float(cant_barras),
            "peso_total_kg": float(peso_total),
        }

        return ResultadoPresupuesto(
            rubro="estructura_metalica",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata=metadata,
            advertencias=[],
        )


registrar(CalcEstructuraMetalica())