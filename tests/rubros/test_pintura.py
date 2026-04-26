"""Tests para src/rubros/pintura.py"""
from __future__ import annotations
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.pintura import ParamsPintura
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["pintura"].calcular(ParamsPintura(**kwargs), EMPRESA)

class TestCasosBase:
    def test_interior(self):
        r = _calc(superficie_m2=50.0, tipo="interior", manos=2)
        assert r.total > 0

    def test_exterior(self):
        r = _calc(superficie_m2=50.0, tipo="exterior", manos=2)
        assert r.total > 0

    def test_invariante_suma(self):
        r = _calc(superficie_m2=50.0, tipo="interior", manos=2)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(superficie_m2=50.0, tipo="interior", manos=2)
        for p in r.partidas:
            assert p.subtotal > 0

class TestPropiedades:
    @given(sup=st.floats(min_value=5.0, max_value=200.0))
    @settings(max_examples=10)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup, tipo="interior", manos=2)
        r2 = _calc(superficie_m2=sup, tipo="interior", manos=2)
        assert r1.total == r2.total