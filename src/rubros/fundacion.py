"""Rubro: Fundación."""
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


class ParamsFundacion(BaseModel):
    tipo: Literal["zapata_aislada", "viga_fundacion"] = "zapata_aislada"
    largo_m: PositiveFloat = Field(0.80, description="Largo Zapata aislada")
    ancho_m: PositiveFloat = Field(0.80, description="Ancho Zapata aislada")
    alto_m: float = Field(0.50, ge=0.30, le=1.50, description="Alto Zapata")
    cantidad: int = Field(1, ge=1, le=200, description="Cantidad de zaptas")
    longitud_ml: float = Field(0.0, ge=0.0, description="Longitud viga fundacion")
    base_cm: int = Field(40, ge=25, le=80, description="Base viga fundacion cm")
    alto_m_viga: float = Field(0.50, ge=0.30, le=1.50, description="Alto viga fundacion")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcFundacion:
    accion = "fundacion"
    schema_params = ParamsFundacion

    @staticmethod
    def calcular(params: ParamsFundacion, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        if params.tipo == "zapata_aislada":
            largo = Decimal(str(params.largo_m))
            ancho = Decimal(str(params.ancho_m))
            alto = Decimal(str(params.alto_m))
            cantidad = Decimal(str(params.cantidad))
            volumen_m3 = _q(largo * ancho * alto * cantidad)
            alto_viga = Decimal("0")
        else:
            base = Decimal(str(params.base_cm)) / Decimal("100")
            alto_viga = Decimal(str(params.alto_m_viga))
            longitud = Decimal(str(params.longitud_ml))
            volumen_m3 = _q(base * alto_viga * longitud)
            largo = Decimal("0")
            ancho = Decimal("0")
            cantidad = Decimal("0")

        # H21 dosificación
        cemento = Decimal(ceil(volumen_m3 * Decimal("7")))
        arena = _q(volumen_m3 * Decimal("0.45"))
        piedra = _q(volumen_m3 * Decimal("0.65"))
        plast = Decimal(max(1, ceil(volumen_m3 / Decimal("5"))))

        # Hierro 8mm: coeficiente 80 kg/m³
        # Barra 8mm 12m pesa: 0.395 kg/m * 12m = 4.74 kg/barra
        cant_barras_8 = Decimal(ceil(float(volumen_m3) * 80 / 4.74))

        # Alambre: 0.5 kg/m3
        cant_alambre = _q(volumen_m3 * Decimal("0.5"))

        # Fundaciones NO llevan tablones

        # MO por m3
        p_mo = precio_mano_obra(datos, "FUNDACION")
        costo_mo = _q(p_mo * volumen_m3)

        # Partidas (7 sin tablones)
        partidas = [
            Partida(
                concepto="Cemento portland",
                cantidad=cemento,
                unidad="u",
                precio_unitario=precio_material(datos, "CEMENTO_PORTLAND"),
                subtotal=_q(cemento * precio_material(datos, "CEMENTO_PORTLAND")),
                categoria="material",
            ),
            Partida(
                concepto="Arena gruesa",
                cantidad=arena,
                unidad="m3",
                precio_unitario=precio_material(datos, "ARENA_GRUESA"),
                subtotal=_q(arena * precio_material(datos, "ARENA_GRUESA")),
                categoria="material",
            ),
            Partida(
                concepto="Piedra partida 6-12mm",
                cantidad=piedra,
                unidad="m3",
                precio_unitario=precio_material(datos, "PIEDRA_6_12"),
                subtotal=_q(piedra * precio_material(datos, "PIEDRA_6_12")),
                categoria="material",
            ),
            Partida(
                concepto="Plastificante Hercal",
                cantidad=plast,
                unidad="u",
                precio_unitario=precio_material(datos, "PLASTIFICANTE_HERCAL"),
                subtotal=_q(plast * precio_material(datos, "PLASTIFICANTE_HERCAL")),
                categoria="material",
            ),
            Partida(
                concepto="Hierro 8mm",
                cantidad=cant_barras_8,
                unidad="u",
                precio_unitario=precio_material(datos, "HIERRO_8"),
                subtotal=_q(cant_barras_8 * precio_material(datos, "HIERRO_8")),
                categoria="material",
            ),
            Partida(
                concepto="Alambre de atar",
                cantidad=cant_alambre,
                unidad="kg",
                precio_unitario=precio_material(datos, "ALAMBRE_ATADO"),
                subtotal=_q(cant_alambre * precio_material(datos, "ALAMBRE_ATADO")),
                categoria="material",
            ),
            Partida(
                concepto="MO fundacion",
                cantidad=volumen_m3,
                unidad="m3",
                precio_unitario=p_mo,
                subtotal=costo_mo,
                categoria="mano_obra",
            ),
        ]

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        metadata = {
            "volumen_m3": float(volumen_m3),
            "tipo": params.tipo,
        }
        if params.tipo == "zapata_aislada":
            metadata["largo_m"] = params.largo_m
            metadata["ancho_m"] = params.ancho_m
            metadata["alto_m"] = params.alto_m
            metadata["cantidad"] = params.cantidad
        else:
            metadata["longitud_ml"] = params.longitud_ml
            metadata["base_cm"] = params.base_cm
            metadata["alto_m"] = params.alto_m_viga

        return ResultadoPresupuesto(
            rubro="fundacion",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata=metadata,
            advertencias=[],
        )


registrar(CalcFundacion())