"""Rubro: Viga y encadenado de hormigón armado."""
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


class ParamsVigaEncadenado(BaseModel):
    longitud_ml: PositiveFloat
    base_cm: int = Field(20, ge=15, le=50)
    alto_cm: int = Field(30, ge=20, le=60)
    tipo: Literal["encadenado", "viga_dintel"] = "encadenado"


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcVigaEncadenado:
    accion = "viga_encadenado"
    schema_params = ParamsVigaEncadenado

    @staticmethod
    def calcular(params: ParamsVigaEncadenado, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        base = Decimal(str(params.base_cm)) / Decimal("100")
        alto = Decimal(str(params.alto_cm)) / Decimal("100")
        longitud = Decimal(str(params.longitud_ml))

        # Volumen en m³
        volumen_m3 = _q(base * alto * longitud)

        # H21: materiales para hormigón
        cemento = Decimal(ceil(volumen_m3 * Decimal("7")))  # bolsas
        arena = _q(volumen_m3 * Decimal("0.45"))  # m3
        piedra = _q(volumen_m3 * Decimal("0.65"))  # m3
        plast = Decimal(max(1, ceil(volumen_m3 / Decimal("5"))))  # bidones

        # Hierro 12mm longitudinal: 4 barras corridas (2 arriba + 2 abajo)
        # 1 barra = 12m, 11m útiles
        cant_barras_12 = Decimal(ceil(float(longitud) / 11.0) * 4)

        # Hierro 6mm estribos: 1 cada 20cm
        estribos_total = ceil(float(longitud) / 0.20)
        perim_estribo = Decimal("2") * (base + alto) + Decimal("0.16")
        ml_hierro6 = Decimal(str(estribos_total)) * perim_estribo
        cant_barras_6 = Decimal(ceil(float(ml_hierro6) / 11.0))

        # Alambre de atar: 0.5 kg por m³
        cant_alambre = _q(volumen_m3 * Decimal("0.5"))

        # Tablones encofrado
        m2_encofrado = _q((Decimal("2") * alto + base) * longitud * Decimal("1.10"))
        cant_tablones = Decimal(ceil(float(m2_encofrado) / 0.75))

        # Mano de obra
        p_mo = precio_mano_obra(datos, "VIGA_ENCADENADO")
        costo_mo = _q(p_mo * volumen_m3)

        # Partidas
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
                concepto="Hierro 12mm longitudinal",
                cantidad=cant_barras_12,
                unidad="u",
                precio_unitario=precio_material(datos, "HIERRO_12"),
                subtotal=_q(cant_barras_12 * precio_material(datos, "HIERRO_12")),
                categoria="material",
            ),
            Partida(
                concepto="Hierro 6mm estribos",
                cantidad=cant_barras_6,
                unidad="u",
                precio_unitario=precio_material(datos, "HIERRO_6"),
                subtotal=_q(cant_barras_6 * precio_material(datos, "HIERRO_6")),
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
                concepto="Tablon encofrado",
                cantidad=cant_tablones,
                unidad="u",
                precio_unitario=precio_material(datos, "TABLON_PINO"),
                subtotal=_q(cant_tablones * precio_material(datos, "TABLON_PINO")),
                categoria="material",
            ),
            Partida(
                concepto="MO vigas encadenado",
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

        return ResultadoPresupuesto(
            rubro="viga_encadenado",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={
                "volumen_m3": float(volumen_m3),
                "longitud_ml": params.longitud_ml,
                "base_cm": params.base_cm,
                "alto_cm": params.alto_cm,
                "tipo": params.tipo,
            },
            advertencias=[],
        )


registrar(CalcVigaEncadenado())