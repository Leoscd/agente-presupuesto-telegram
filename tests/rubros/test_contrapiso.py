"""Tests determinísticos para contrapiso sobre datos de estudio_ramos."""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from src.rubros import REGISTRY
from src.rubros.contrapiso import ParamsContrapiso


EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    params = ParamsContrapiso(**kwargs)
    return REGISTRY["contrapiso"].calcular(params, EMPRESA)


def test_contrapiso_20m2_8cm():
    """m3 = 20 * 0.08 = 1.6 m3. Cemento = ceil(1.6*4) = 7"""
    r = _calc(superficie_m2=20, espesor_cm=8)

    assert r.metadata["superficie_m2"] == 20
    assert r.metadata["volumen_m3"] == 1.6

    cemento = next(p for p in r.partidas if "cemento" in p.concepto.lower())
    assert cemento.cantidad == 7


def test_espesor_minimo():
    """espesor_cm muy pequeño no debe crashear"""
    r = _calc(superficie_m2=10, espesor_cm=5)
    assert r.total > 0


def test_invariante_suma_partidas():
    r = _calc(superficie_m2=20, espesor_cm=8)
    suma = sum((p.subtotal for p in r.partidas), Decimal("0"))
    assert suma == r.total


@given(
    superficie=st.decimals(min_value=Decimal("5"), max_value=Decimal("50")), 
    espesor=st.floats(min_value=5.0, max_value=15.0)
)
def test_propiedad_monotonia(superficie, espesor):
    r1 = _calc(superficie_m2=float(superficie), espesor_cm=float(espesor))
    r2 = _calc(superficie_m2=float(superficie) + 10, espesor_cm=float(espesor))
    assert r2.total >= r1.total