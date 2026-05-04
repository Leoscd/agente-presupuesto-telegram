"""Rubro: Escalera de hormigón armado."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil
import math

from pydantic import BaseModel, Field, PositiveFloat

from src.datos.loader import (
    cargar_empresa,
    precio_mano_obra,
    precio_material,
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsEscaleraHormigon(BaseModel):
    cantidad_escalones: int = Field(..., ge=4, le=30)
    ancho_m: float = Field(1.20, ge=0.80, le=3.0)
    huella_cm: float = Field(28.0, ge=22.0, le=35.0)
    contrahuela_cm: float = Field(18.0, ge=15.0, le=22.0)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class _CalcEscaleraHormigon:
    accion = "escalera_hormigon"
    schema_params = ParamsEscaleraHormigon

    def calcular(self, params: ParamsEscaleraHormigon, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        faltantes = materiales_faltantes(datos, [
            "CEMENTO_PORTLAND", "ARENA_GRUESA", "PIEDRA_6_12",
            "PLASTIFICANTE_HERCAL", "HIERRO_8",
            "ALAMBRE_ATADO", "TABLON_PINO",
        ])
        if faltantes:
            raise ValueError(
                f"Materiales no disponibles en {empresa_id}: {', '.join(faltantes)}"
            )

        n = params.cantidad_escalones
        ancho = Decimal(str(params.ancho_m))
        huella_m = Decimal(str(params.huella_cm)) / Decimal("100")
        contrahuela_m = Decimal(str(params.contrahuela_cm)) / Decimal("100")

        altura_total_m = contrahuela_m * Decimal(str(n))
        longitud_horiz_m = huella_m * Decimal(str(n))

        # Longitud diagonal de la losa inclinada
        long_diagonal = Decimal(str(math.sqrt(
            float(altura_total_m) ** 2 + float(longitud_horiz_m) ** 2
        )))

        espesor_losa = Decimal("0.12")  # 12cm constante

        # Volumen losa inclinada
        vol_losa = long_diagonal * ancho * espesor_losa

        # Volumen escalones (prismas triangulares)
        vol_escalones = Decimal("0.5") * huella_m * contrahuela_m * Decimal(str(n)) * ancho

        volumen_m3 = _q(vol_losa + vol_escalones)

        # H21 dosificación
        cemento = Decimal(ceil(volumen_m3 * Decimal("7")))
        arena = _q(volumen_m3 * Decimal("0.45"))
        piedra = _q(volumen_m3 * Decimal("0.65"))
        plast = Decimal(max(1, ceil(volumen_m3 / Decimal("5"))))

        # Hierro 8mm: coeficiente 17 barras por m³
        cant_barras_8 = Decimal(ceil(float(volumen_m3) * 17))

        # Tablones encofrado: losa inferior + laterales
        m2_enc = _q(long_diagonal * ancho * Decimal("2.20"))  # factor 2.2 incluye laterales
        cant_tablones = Decimal(ceil(float(m2_enc) / 0.75))

        # Alambre: 0.5 kg/m3
        cant_alambre = _q(volumen_m3 * Decimal("0.5"))

        # MO: precio ESCALERA_HORMIGON es por escalón (u), no por m3
        p_mo = precio_mano_obra(datos, "ESCALERA_HORMIGON")
        costo_mo = _q(p_mo * Decimal(str(n)))

        # Partidas (8)
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
                concepto="Tablon encofrado",
                cantidad=cant_tablones,
                unidad="u",
                precio_unitario=precio_material(datos, "TABLON_PINO"),
                subtotal=_q(cant_tablones * precio_material(datos, "TABLON_PINO")),
                categoria="material",
            ),
            Partida(
                concepto="MO escalera",
                cantidad=Decimal(str(n)),
                unidad="u",
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
            "cantidad_escalones": n,
            "altura_total_m": float(altura_total_m),
            "ancho_m": params.ancho_m,
        }

        return ResultadoPresupuesto(
            rubro="escalera_hormigon",
            partidas=partidas,
            subtotal_materiales=_q(sub_mat),
            subtotal_mano_obra=_q(sub_mo),
            total=_q(total),
            metadata=metadata,
            advertencias=[],
        )


registrar(_CalcEscaleraHormigon())