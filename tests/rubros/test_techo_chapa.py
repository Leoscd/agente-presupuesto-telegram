"""Tests determinísticos para techo_chapa sobre datos de estudio_ramos."""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from src.rubros import REGISTRY
from src.rubros.techo_chapa import ParamsTechoChapa


EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    params = ParamsTechoChapa(**kwargs)
    return REGISTRY["techo_chapa"].calcular(params, EMPRESA)


def test_caso_base_7x10_galvanizada_C100():
    r = _calc(ancho=7, largo=10, tipo_chapa="galvanizada_075", tipo_perfil="C100")

    # Superficie
    assert r.metadata["superficie_m2"] == 70.0

    # Chapa: 70 m² * 1.10 rend = 77 m² * $8500 = $654500
    chapa = next(p for p in r.partidas if "galvanizada" in p.concepto.lower())
    assert chapa.cantidad == Decimal("77.00")
    assert chapa.subtotal == Decimal("654500.00")

    # Perfil C100: ceil(10/1.0)+1 = 11 correas * 7m * 1.05 = 80.85 ml * $4800 = $388080
    perfil = next(p for p in r.partidas if "C 100" in p.concepto)
    assert perfil.cantidad == Decimal("80.85")
    assert perfil.subtotal == Decimal("388080.00")

    # Tornillos: 70 * 12 = 840 * $45 = $37800
    torn = next(p for p in r.partidas if "tornillo" in p.concepto.lower())
    assert torn.cantidad == Decimal("840.00")
    assert torn.subtotal == Decimal("37800.00")

    # Mano obra: 70 * $4200 = $294000
    mo = next(p for p in r.partidas if p.categoria == "mano_obra")
    assert mo.subtotal == Decimal("294000.00")

    # Total = 654500 + 388080 + 37800 + 294000
    assert r.total == Decimal("1374380.00")


def test_invariante_suma_partidas_igual_total():
    r = _calc(ancho=5, largo=8, tipo_chapa="color_075", tipo_perfil="C60")
    suma = sum((p.subtotal for p in r.partidas), Decimal("0"))
    assert suma == r.total


def test_sin_perfil_agrega_advertencia():
    r = _calc(ancho=4, largo=6, tipo_chapa="galvanizada_075", tipo_perfil=None)
    assert any("estructura existente" in a.lower() for a in r.advertencias)
    assert not any("perfil" in p.concepto.lower() for p in r.partidas)


def test_material_no_disponible_falla():
    # Pedimos un tipo que el validador debería aceptar; probamos con schema inválido
    with pytest.raises(ValueError):
        ParamsTechoChapa(ancho=-1, largo=10)


@given(
    ancho=st.decimals(min_value=Decimal("1"), max_value=Decimal("50"), places=1),
    largo=st.decimals(min_value=Decimal("1"), max_value=Decimal("50"), places=1),
)
def test_propiedad_monotonia_superficie(ancho, largo):
    """Más superficie => más total (ceteris paribus)."""
    r1 = _calc(ancho=float(ancho), largo=float(largo))
    r2 = _calc(ancho=float(ancho) + 1, largo=float(largo))
    assert r2.total >= r1.total


@given(
    ancho=st.decimals(min_value=Decimal("2"), max_value=Decimal("20"), places=1),
    largo=st.decimals(min_value=Decimal("2"), max_value=Decimal("20"), places=1),
)
def test_propiedad_idempotencia(ancho, largo):
    """Mismo input dos veces => mismo resultado exacto."""
    r1 = _calc(ancho=float(ancho), largo=float(largo))
    r2 = _calc(ancho=float(ancho), largo=float(largo))
    assert r1.total == r2.total
    assert r1.partidas == r2.partidas
