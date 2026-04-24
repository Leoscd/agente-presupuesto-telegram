"""Tests determinísticos para mampostería sobre datos de estudio_ramos."""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from src.rubros import REGISTRY
from src.rubros.mamposteria import ParamsMamposteria


EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    params = ParamsMamposteria(**kwargs)
    return REGISTRY["mamposteria"].calcular(params, EMPRESA)


def test_muro_hueco_12_5x3():
    """15m2 * 36 ladrillos/m2 * 1.05 = 567 ladrillos"""
    r = _calc(largo=5, alto=3, tipo="hueco_12")

    assert r.metadata["superficie_m2"] == 15.0

    # Verificar que existe partida de ladrillo
    ladrillo = next(p for p in r.partidas if "ladrillo" in p.concepto.lower() and "hueco" in p.concepto.lower())
    assert ladrillo.cantidad == 567


def test_muro_comun_sin_plastificante():
    """tipo='comun' debe usar ladrillo común, no plastificante"""
    r = _calc(largo=3, alto=2.5, tipo="comun")

    # Debe tener ladrillo común
    lad_comun = next(p for p in r.partidas if "comun" in p.concepto.lower())
    assert lad_comun is not None


def test_invariante_suma_partidas_igual_total():
    """Suma de subtotales debe igualar total"""
    r = _calc(largo=5, alto=3, tipo="hueco_12")
    suma = sum((p.subtotal for p in r.partidas), Decimal("0"))
    assert suma == r.total


def test_alto_cero_falla():
    """alto=0 debe lanzar ValidationError"""
    with pytest.raises(Exception):  # pydantic validation error
        _calc(largo=5, alto=0, tipo="hueco_12")


@given(
    largo=st.decimals(min_value=Decimal("1"), max_value=Decimal("20"), places=1),
    alto=st.decimals(min_value=Decimal("1"), max_value=Decimal("5"), places=1),
)
def test_propiedad_monotonia(largo, alto):
    """Más superficie => más total"""
    r1 = _calc(largo=float(largo), alto=float(alto))
    r2 = _calc(largo=float(largo) + 1, alto=float(alto))
    assert r2.total >= r1.total


@given(
    largo=st.decimals(min_value=Decimal("2"), max_value=Decimal("10"), places=1),
    alto=st.decimals(min_value=Decimal("1"), max_value=Decimal("4"), places=1),
)
def test_propiedad_idempotencia(largo, alto):
    """Mismo input dos veces => mismo resultado"""
    r1 = _calc(largo=float(largo), alto=float(alto))
    r2 = _calc(largo=float(largo), alto=float(alto))
    assert r1.total == r2.total