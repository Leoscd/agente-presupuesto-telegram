"""Tests para instalacion_sanitaria - AGENT_TASKS.md TAREA 3"""
from __future__ import annotations
from decimal import Decimal
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.instalacion_sanitaria import ParamsInstalacionSanitaria
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    return REGISTRY["instalacion_sanitaria"].calcular(ParamsInstalacionSanitaria(**kwargs), EMPRESA)


class TestCasosBase:
    def test_1_bano(self):
        r = _calc(cantidad_banos=1)
        assert r.metadata["cantidad_banos"] == 1

    def test_2_banos(self):
        r = _calc(cantidad_banos=2)
        assert r.metadata["cantidad_banos"] == 2

    def test_bano_cocina(self):
        r = _calc(cantidad_banos=1, cantidad_cocinas=1)
        assert r.total > 0

    def test_invariante_suma(self):
        r = _calc(cantidad_banos=1)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(cantidad_banos=1)
        for p in r.partidas:
            assert p.subtotal > 0


class TestValidacion:
    def test_banos_minimo(self):
        with pytest.raises(Exception):
            _calc(cantidad_banos=0)


class TestPropiedades:
    @given(banos=st.integers(min_value=1, max_value=5))
    @settings(max_examples=10)
    def test_idempotencia(self, banos):
        r1 = _calc(cantidad_banos=banos)
        r2 = _calc(cantidad_banos=banos)
        assert r1.total == r2.total