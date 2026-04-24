"""Tests para revoque_fino - AGENT_TASKS.md TAREA 3"""
from __future__ import annotations
from decimal import Decimal
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.revoque_fino import ParamsRevoqueFino
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    return REGISTRY["revoque_fino"].calcular(ParamsRevoqueFino(**kwargs), EMPRESA)


class TestCasosBase:
    def test_caso_base(self):
        r = _calc(superficie_m2=20, espesor_cm=0.5)
        assert r.metadata["superficie_m2"] == 20.0
        assert r.total > 0

    def test_yeso_necesario(self):
        r = _calc(superficie_m2=10)
        tiene_yeso = any("yeso" in p.concepto.lower() for p in r.partidas)
        assert tiene_yeso

    def test_invariante_suma(self):
        r = _calc(superficie_m2=30)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(superficie_m2=20)
        for p in r.partidas:
            assert p.subtotal > 0


class TestValidacion:
    def test_espesor_max_falla(self):
        with pytest.raises(Exception):
            _calc(superficie_m2=20, espesor_cm=5.0)


class TestPropiedades:
    @given(sup=st.floats(min_value=1.0, max_value=100.0))
    @settings(max_examples=10)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup)
        r2 = _calc(superficie_m2=sup)
        assert r1.total == r2.total