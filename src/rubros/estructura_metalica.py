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
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsEstructuraMetalica(BaseModel):
    longitud_ml: PositiveFloat
    tipo_perfil: Literal["IPN_120"] = "IPN_120"
    incluye_pintura_anticorrosiva: bool = Field(True, description="Incluye pintura anticorrosiva")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class _CalcEstructuraMetalica:
    accion = "estructura_metalica"
    schema_params = ParamsEstructuraMetalica

    CODIGO_PERFIL = {
        "IPN_120": "PERFIL_IPN_120",
    }

    def calcular(self, params: ParamsEstructuraMetalica, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        cod_perfil = _CalcEstructuraMetalica.CODIGO_PERFIL[params.tipo_perfil]
        codigos_usados = [cod_perfil, "ELECTRODO_E6013"]
        if params.incluye_pintura_anticorrosiva:
            codigos_usados.append("PINTURA_ANTICORR")
        faltantes = materiales_faltantes(datos, codigos_usados)
        if faltantes:
            raise ValueError(
                f"Materiales no disponibles en {empresa_id}: {', '.join(faltantes)}"
            )

        long = Decimal(str(params.longitud_ml))

        # Perfil: barras de 12m
        cant_barras = Decimal(ceil(float(long) / 12.0))
        p_perfil = precio_material(datos, cod_perfil)

        partidas: list[Partida] = [
            Partida(
                concepto=f"Perfil {params.tipo_perfil} barra 12m",
                cantidad=cant_barras,
                unidad="u",
                precio_unitario=p_perfil,
                subtotal=_q(cant_barras * p_perfil),
                categoria="material",
            )
        ]

        # Pintura anticorrosiva si aplica
        if params.incluye_pintura_anticorrosiva:
            # 0.45 m2/ml de perfil, rendimiento 10 m2/L, lata 4L
            m2_perfil = _q(long * Decimal("0.45"))
            litros_ant = m2_perfil / Decimal("10")
            cant_latas = Decimal(ceil(float(litros_ant) / 4.0))
            p_pintura = precio_material(datos, "PINTURA_ANTICORR")

            partidas.append(
                Partida(
                    concepto="Pintura anticorrosiva lata 4L",
                    cantidad=cant_latas,
                    unidad="u",
                    precio_unitario=p_pintura,
                    subtotal=_q(cant_latas * p_pintura),
                    categoria="material",
                )
            )

        # Electrodos: 3 por metro lineal, caja 50u
        cant_cajas_elec = Decimal(ceil(float(long) * 3 / 50))
        p_elec = precio_material(datos, "ELECTRODO_E6013")

        partidas.append(
            Partida(
                concepto="Electrodos E6013 caja 50u",
                cantidad=cant_cajas_elec,
                unidad="u",
                precio_unitario=p_elec,
                subtotal=_q(cant_cajas_elec * p_elec),
                categoria="material",
            )
        )

        # Mano de obra
        p_mo = precio_mano_obra(datos, "ESTRUCTURA_METALICA")
        costo_mo = _q(p_mo * long)

        partidas.append(
            Partida(
                concepto="MO estructura metalica",
                cantidad=long,
                unidad="ml",
                precio_unitario=p_mo,
                subtotal=costo_mo,
                categoria="mano_obra",
            )
        )

        sub_mat = sum(
            (p.subtotal for p in partidas if p.categoria == "material"), Decimal("0")
        )
        sub_mo = sum(
            (p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0")
        )
        total = sub_mat + sub_mo

        metadata = {
            "longitud_ml": params.longitud_ml,
            "tipo_perfil": params.tipo_perfil,
            "incluye_pintura_anticorrosiva": params.incluye_pintura_anticorrosiva,
            "cant_barras": float(cant_barras),
        }

        return ResultadoPresupuesto(
            rubro="estructura_metalica",
            partidas=partidas,
            subtotal_materiales=_q(sub_mat),
            subtotal_mano_obra=_q(sub_mo),
            total=_q(total),
            metadata=metadata,
            advertencias=[],
        )


registrar(_CalcEstructuraMetalica())