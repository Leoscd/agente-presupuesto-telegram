"""Rubro: Instalación sanitaria."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil

from pydantic import BaseModel, Field

from src.datos.loader import cargar_empresa, precio_mano_obra, precio_material
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


class ParamsInstalacionSanitaria(BaseModel):
    cantidad_banos: int = Field(1, ge=1, le=10)
    cantidad_cocinas: int = Field(0, ge=0, le=5)
    metros_lineales_agua_fria: float = Field(0.0, ge=0)
    metros_lineales_desague: float = Field(0.0, ge=0)
    tipo_cano: str = Field("pvc")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CalcInstalacionSanitaria:
    accion = "instalacion_sanitaria"
    schema_params = ParamsInstalacionSanitaria

    @staticmethod
    def calcular(params: ParamsInstalacionSanitaria, empresa_id: str) -> ResultadoPresupuesto:
        datos = cargar_empresa(empresa_id)

        # Metros de agua fría: si 0, calcular por cantidad de baños/cocinas
        ml_agua = params.metros_lineales_agua_fria
        if ml_agua == 0:
            ml_agua = params.cantidad_banos * 8 + params.cantidad_cocinas * 5

        # Metros de desagüe: si 0 calcular
        ml_desague = params.metros_lineales_desague
        if ml_desague == 0:
            ml_desague = (params.cantidad_banos + params.cantidad_cocinas) * 10

        # Codos y uniones: 30% del total de metros
        accesorios_ml = (ml_agua + ml_desague) * Decimal("0.3")

        # Materiales
        partidas = []

        # Caño PVC agua 32mm
        partidas.append(Partida(
            concepto="Caño PVC presión 32mm",
            cantidad=ml_agua,
            unidad="ml",
            precio_unitario=precio_material(datos, "CANO_PVC_32"),
            subtotal=ml_agua * precio_material(datos, "CANO_PVC_32"),
            categoria="material"
        ))

        # Caño PVC desagüe 50mm
        partidas.append(Partida(
            concepto="Caño PVC desague 50mm",
            cantidad=ml_desague,
            unidad="ml",
            precio_unitario=precio_material(datos, "CANO_PVC_50"),
            subtotal=ml_desague * precio_material(datos, "CANO_PVC_50"),
            categoria="material"
        ))

        # Codos y	uniones
        partidas.append(Partida(
            concepto="Codos y uniones PVC",
            cantidad=accesorios_ml,
            unidad="ml",
            precio_unitario=precio_material(datos, "CODOS_PVC_32"),
            subtotal=accesorios_ml * precio_material(datos, "CODOS_PVC_32"),
            categoria="material"
        ))

        # Cinta teflón
        cant_rollo = ceil((ml_agua + ml_desague) / Decimal("50"))
        partidas.append(Partida(
            concepto="Cinta teflón",
            cantidad=cant_rollo,
            unidad="u",
            precio_unitario=precio_material(datos, "SELLADOR_TEFLON"),
            subtotal=cant_rollo * precio_material(datos, "SELLADOR_TEFLON"),
            categoria="material"
        ))

        # Mano de obra (por baño/cocina, no por m2)
        unidades = params.cantidad_banos + params.cantidad_cocinas
        costo_mo = precio_mano_obra(datos, "INSTALACION_SANITARIA") * Decimal(str(unidades))
        
        partidas.append(Partida(
            concepto="MO instalación sanitaria",
            cantidad=unidades,
            unidad="u",
            precio_unitario=costo_mo / Decimal(str(unidades)),
            subtotal=costo_mo,
            categoria="mano_obra"
        ))

        # Validar materiales
        codigos = [p.concepto.split()[0] for p in partidas]
        faltantes = materiales_faltantes(datos, codigos)

        total = sum((p.subtotal for p in partidas), Decimal("0"))
        sub_mat = sum((p.subtotal for p in partidas if p.categoria == "material"), Decimal("0"))
        sub_mo = sum((p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0"))

        return ResultadoPresupuesto(
            rubro="instalacion_sanitaria",
            partidas=partidas,
            subtotal_materiales=sub_mat,
            subtotal_mano_obra=sub_mo,
            total=total,
            metadata={
                "cantidad_banos": params.cantidad_banos,
                "cantidad_cocinas": params.cantidad_cocinas,
                "ml_agua_fria": ml_agua,
                "ml_desague": ml_desague,
            },
            advertencias=[f"Materiales no disponibles: {faltantes}"] if faltantes else [],
        )


registrar(CalcInstalacionSanitaria())