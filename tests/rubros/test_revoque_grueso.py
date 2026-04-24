"""Tests determinísticos para revoque_grueso sobre datos de estudio_ramos."""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, strategies as st

from src.rubros import REGISTRY
from src.rubros.revoque_grueso import ParamsRevoqueGrueso


EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    params = ParamsRevoqueGrueso(**kwargs)
    return REGISTRY["revoque_grueso"].calcular(params, EMPRESA)


def test_revoque_30m2():
    """30m2, espesor=1.5cm -> m3=0.45. Plastificante: ceil(30/30)=1"""
    r = _calc(superficie_m2=30, espesor_cm=1.5)

    assert r.metadata["superficie_m2"] == 30

    # Plastificante: ceil(30/30) = 1 bidón
    plast = next(p for p in r.partidas if "plastificante" in p.concepto.lower())
    assert plast.cantidad == 1


def test_invariante_suma_partidas():
    r = _calc(superficie_m2=30, espesor_cm=1.5)
    suma = sum((p.subtotal for p in r.partidas), Decimal("0"))
    assert suma == r.total


@given(
    superficie=st.decimals(min_value=Decimal("5"), max_value=Decimal("50")),
)
def test_propiedad_monotonia(superficie):
    r1 = _calc(superficie_m2=float(superficie))
    r2 = _calc(superficie_m2=float(superficie) + 10)
    assert r2.total >= r1.total