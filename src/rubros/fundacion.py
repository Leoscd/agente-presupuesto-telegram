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
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsFundacion(BaseModel):
    tipo: Literal["zapata_aislada", "viga_fundacion"] = "zapata_aislada"
    largo_m: PositiveFloat = Field(0.80, description="Largo Zapata aislada")
    ancho_m: PositiveFloat = Field(0.80, description="Ancho Zapata aislada")
    alto_m: float = Field(0.50, ge=0.30, le=1.50, description="Alto zapata o viga fundacion")
    cantidad: int = Field(1, ge=1, le=200, description="Cantidad de zaptas")
    longitud_ml: float = Field(0.0, ge=0.0, description="Longitud viga fundacion")
    base_cm: int = Field(40, ge=25, le=80, description="Base viga fundacion cm")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class _CalcFundacion:
    accion = "fundacion"
    schema_params = ParamsFundacion

    def calcular(self, params: ParamsFundacion, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        codigos_usados = [
            "CEMENTO_PORTLAND",
            "ARENA_GRUESA",
            "PIEDRA_6_12",
            "PLASTIFICANTE_HERCAL",
            "HIERRO_8",
            "ALAMBRE_ATADO",
        ]
        faltantes = materiales_faltantes(datos, codigos_usados)
        if faltantes:
            raise ValueError(
                f"Materiales no disponibles en {empresa_id}: {', '.join(faltantes)}"
            )

        if params.tipo == "zapata_aislada":
            largo = Decimal(str(params.largo_m))
            ancho = Decimal(str(params.ancho_m))
            alto = Decimal(str(params.alto_m))
            cantidad = Decimal(str(params.cantidad))
            volumen_m3 = _q(largo * ancho * alto * cantidad)
            alto_viga = Decimal("0")
        else:
            base = Decimal(str(params.base_cm)) / Decimal("100")
            alto_viga = Decimal(str(params.alto_m))
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

        p_cemento = precio_material(datos, "CEMENTO_PORTLAND")
        p_arena = precio_material(datos, "ARENA_GRUESA")
        p_piedra = precio_material(datos, "PIEDRA_6_12")
        p_plast = precio_material(datos, "PLASTIFICANTE_HERCAL")
        p_hierro8 = precio_material(datos, "HIERRO_8")
        p_alambre = precio_material(datos, "ALAMBRE_ATADO")

        # Partidas (7 sin tablones)
        partidas = [
            Partida(
                concepto="Cemento portland",
                cantidad=cemento,
                unidad="u",
                precio_unitario=p_cemento,
                subtotal=_q(cemento * p_cemento),
                categoria="material",
            ),
            Partida(
                concepto="Arena gruesa",
                cantidad=arena,
                unidad="m3",
                precio_unitario=p_arena,
                subtotal=_q(arena * p_arena),
                categoria="material",
            ),
            Partida(
                concepto="Piedra partida 6-12mm",
                cantidad=piedra,
                unidad="m3",
                precio_unitario=p_piedra,
                subtotal=_q(piedra * p_piedra),
                categoria="material",
            ),
            Partida(
                concepto="Plastificante Hercal",
                cantidad=plast,
                unidad="u",
                precio_unitario=p_plast,
                subtotal=_q(plast * p_plast),
                categoria="material",
            ),
            Partida(
                concepto="Hierro 8mm",
                cantidad=cant_barras_8,
                unidad="u",
                precio_unitario=p_hierro8,
                subtotal=_q(cant_barras_8 * p_hierro8),
                categoria="material",
            ),
            Partida(
                concepto="Alambre de atar",
                cantidad=cant_alambre,
                unidad="kg",
                precio_unitario=p_alambre,
                subtotal=_q(cant_alambre * p_alambre),
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
            metadata["alto_m"] = params.alto_m

        return ResultadoPresupuesto(
            rubro="fundacion",
            partidas=partidas,
            subtotal_materiales=_q(sub_mat),
            subtotal_mano_obra=_q(sub_mo),
            total=_q(total),
            metadata=metadata,
            advertencias=[],
        )


registrar(_CalcFundacion())