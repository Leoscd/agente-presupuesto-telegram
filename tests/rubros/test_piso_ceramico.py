"""Tests para src/rubros/piso_ceramico.py"""
from __future__ import annotations

from decimal import Decimal
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.piso_ceramico import ParamsPisoCeramico
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    return REGISTRY["piso_ceramico"].calcular(ParamsPisoCeramico(**kwargs), EMPRESA)


class TestCasosBase:
    def test_caso_base(self):
        r = _calc(superficie_m2=20, material="ceramico_45x45")
        assert r.metadata["superficie_m2"] == 20.0
        assert r.total > 0

    def test_porcelanato(self):
        r = _calc(superficie_m2=15, material="porcelanato_60x60")
        assert r.metadata["material"] == "porcelanato_60x60"

    def test_con_zocalo(self):
        r = _calc(superficie_m2=20, incluye_zocalo=True, perimetro_m=20)
        assert r.metadata["incluye_zocalo"] is True

    def test_invariante_suma_igual_total(self):
        r = _calc(superficie_m2=30)
        suma = sum(p.subtotal for p in r.partidas)
        assert suma == r.total

    def test_partidas_positivas(self):
        r = _calc(superficie_m2=20)
        for p in r.partidas:
            assert p.subtotal > 0


class TestMateriales:
    def test_ceramico_30x30(self):
        r = _calc(superficie_m2=10, material="ceramico_30x30")
        assert any("ceramico_30x30" in p.concepto.lower() for p in r.partidas)

    def test_porcelanato_premium(self):
        r = _calc(superficie_m2=10, material="porcelanato_60x60_premium")
        assert any("premium" in p.concepto.lower() for p in r.partidas)


class TestPropiedades:
    @given(sup=st.floats(min_value=5.0, max_value=50.0))
    @settings(max_examples=20)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup)
        r2 = _calc(superficie_m2=sup)
        assert r1.total == r2.total