"""Tests para src/rubros/membrana_impermeabilizante.py"""
from __future__ import annotations
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.membrana_impermeabilizante import ParamsMembrana
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["membrana_impermeabilizante"].calcular(ParamsMembrana(**kwargs), EMPRESA)

class TestCasosBase:
    def test_asfaltica(self):
        r = _calc(superficie_m2=30.0, tipo="membrana_asfaltica", capas=2)
        assert r.metadata["tipo"] == "membrana_asfaltica"
        assert r.total > 0

    def test_liquida(self):
        r = _calc(superficie_m2=30.0, tipo="liquida", capas=2)
        assert r.metadata["tipo"] == "liquida"

    def test_invariante_suma(self):
        r = _calc(superficie_m2=30.0, tipo="membrana_asfaltica", capas=2)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(superficie_m2=30.0, tipo="membrana_asfaltica", capas=2)
        for p in r.partidas:
            assert p.subtotal > 0

class TestPropiedades:
    @given(sup=st.floats(min_value=5.0, max_value=100.0))
    @settings(max_examples=10)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup, tipo="membrana_asfaltica", capas=2)
        r2 = _calc(superficie_m2=sup, tipo="membrana_asfaltica", capas=2)
        assert r1.total == r2.total