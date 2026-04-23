"""Rubro: techo de chapa sobre perfilería C.

Fórmulas:
- m2 = ancho * largo
- chapa_m2 = m2 * rendimiento(chapa)
- correas: una cada `separacion_correa` metros en el sentido del largo, + 1 extra
  cant_perfil_ml = (ceil(largo / separacion) + 1) * ancho * rendimiento(perfil)
- tornillos: aprox 12 por m2 de chapa
- mano de obra: tarifa "TECHO_CHAPA" * m2
"""
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
    rendimiento,
)
from src.datos.validador import materiales_faltantes
from src.rubros.base import Partida, ResultadoPresupuesto, registrar


TipoChapa = Literal["galvanizada_075", "galvanizada_090", "zinc_075", "color_075"]
TipoPerfil = Literal["C60", "C100", "C160"] | None

CODIGO_CHAPA: dict[str, str] = {
    "galvanizada_075": "CHAPA_GALV_075",
    "galvanizada_090": "CHAPA_GALV_090",
    "zinc_075": "CHAPA_ZINC_075",
    "color_075": "CHAPA_COLOR_075",
}
CODIGO_PERFIL: dict[str, str] = {
    "C60": "PERFIL_C60",
    "C100": "PERFIL_C100",
    "C160": "PERFIL_C160",
}
TORNILLOS_POR_M2 = Decimal("12")
SEPARACION_CORREA_M = Decimal("1.0")


class ParamsTechoChapa(BaseModel):
    ancho: PositiveFloat = Field(..., description="Metros")
    largo: PositiveFloat = Field(..., description="Metros")
    tipo_chapa: TipoChapa = "galvanizada_075"
    tipo_perfil: TipoPerfil = "C100"
    separacion_correa_m: float = Field(1.0, gt=0.1, le=2.0)


def _q(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class _CalcTechoChapa:
    accion: str = "techo_chapa"
    schema_params: type[BaseModel] = ParamsTechoChapa

    def calcular(self, params: BaseModel, empresa_id: str) -> ResultadoPresupuesto:
        assert isinstance(params, ParamsTechoChapa)
        datos = cargar_empresa(empresa_id)

        codigos_usados: list[str] = [CODIGO_CHAPA[params.tipo_chapa], "TORNILLO_AUTOP"]
        if params.tipo_perfil:
            codigos_usados.append(CODIGO_PERFIL[params.tipo_perfil])

        faltantes = materiales_faltantes(datos, codigos_usados)
        if faltantes:
            raise ValueError(
                f"Materiales no disponibles en {empresa_id}: {', '.join(faltantes)}"
            )

        ancho = Decimal(str(params.ancho))
        largo = Decimal(str(params.largo))
        sep = Decimal(str(params.separacion_correa_m))
        m2 = ancho * largo

        partidas: list[Partida] = []
        advertencias: list[str] = []

        # --- Chapa ---
        cod_chapa = CODIGO_CHAPA[params.tipo_chapa]
        p_chapa = precio_material(datos, cod_chapa)
        r_chapa = rendimiento(datos, cod_chapa, Decimal("1.10"))
        cant_chapa = _q(m2 * r_chapa)
        sub_chapa = _q(cant_chapa * p_chapa)
        partidas.append(
            Partida(
                concepto=_descripcion(datos, cod_chapa),
                cantidad=cant_chapa,
                unidad="m2",
                precio_unitario=p_chapa,
                subtotal=sub_chapa,
                categoria="material",
            )
        )

        # --- Perfil ---
        if params.tipo_perfil:
            cod_perfil = CODIGO_PERFIL[params.tipo_perfil]
            p_perfil = precio_material(datos, cod_perfil)
            r_perfil = rendimiento(datos, cod_perfil, Decimal("1.05"))
            nro_correas = ceil(float(largo) / float(sep)) + 1
            cant_perfil_ml = _q(Decimal(nro_correas) * ancho * r_perfil)
            sub_perfil = _q(cant_perfil_ml * p_perfil)
            partidas.append(
                Partida(
                    concepto=_descripcion(datos, cod_perfil),
                    cantidad=cant_perfil_ml,
                    unidad="ml",
                    precio_unitario=p_perfil,
                    subtotal=sub_perfil,
                    categoria="material",
                )
            )
        else:
            advertencias.append("Sin perfilería — se asume estructura existente.")

        # --- Tornillos ---
        p_torn = precio_material(datos, "TORNILLO_AUTOP")
        cant_torn = _q((m2 * TORNILLOS_POR_M2).quantize(Decimal("1")))
        sub_torn = _q(cant_torn * p_torn)
        partidas.append(
            Partida(
                concepto=_descripcion(datos, "TORNILLO_AUTOP"),
                cantidad=cant_torn,
                unidad="u",
                precio_unitario=p_torn,
                subtotal=sub_torn,
                categoria="material",
            )
        )

        # --- Mano de obra ---
        p_mo = precio_mano_obra(datos, "TECHO_CHAPA")
        sub_mo = _q(m2 * p_mo)
        partidas.append(
            Partida(
                concepto="Colocación de chapa y perfilería",
                cantidad=_q(m2),
                unidad="m2",
                precio_unitario=p_mo,
                subtotal=sub_mo,
                categoria="mano_obra",
            )
        )

        sub_mat = sum(
            (p.subtotal for p in partidas if p.categoria == "material"), Decimal("0")
        )
        sub_mo_total = sum(
            (p.subtotal for p in partidas if p.categoria == "mano_obra"), Decimal("0")
        )
        total = sub_mat + sub_mo_total

        return ResultadoPresupuesto(
            rubro="Techo de chapa",
            partidas=partidas,
            subtotal_materiales=_q(sub_mat),
            subtotal_mano_obra=_q(sub_mo_total),
            total=_q(total),
            metadata={
                "ancho_m": float(ancho),
                "largo_m": float(largo),
                "superficie_m2": float(m2),
                "tipo_chapa": params.tipo_chapa,
                "tipo_perfil": params.tipo_perfil,
                "separacion_correa_m": float(sep),
            },
            advertencias=advertencias,
        )


def _descripcion(datos: DatosEmpresa, codigo: str) -> str:
    fila = datos.precios_materiales.loc[datos.precios_materiales["codigo"] == codigo]
    if fila.empty:
        return codigo
    return str(fila.iloc[0]["descripcion"])


registrar(_CalcTechoChapa())
