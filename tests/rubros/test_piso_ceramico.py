"""Tests para piso_ceramico - AGENT_TASKS.md TAREA 4"""
from __future__ import annotations

from decimal import Decimal
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.piso_ceramico import ParamsPisoCeramico
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"


def tiene_zocalo(r):
    """Check if result has zocalo partidas."""
    for p in r.partidas:
        # Match both "zocalo" and "zócalo" after removing accents
        c = p.concepto.lower().replace('ó', 'o').replace('á', 'a')
        if 'zocalo' in c:
            return True
    return False


def _calc(**kwargs):
    return REGISTRY["piso_ceramico"].calcular(ParamsPisoCeramico(**kwargs), EMPRESA)


class TestCasosBase:
    def test_piso_sin_zocalo(self):
        r = _calc(superficie_m2=20, material="ceramico_45x45")
        assert tiene_zocalo(r) is False

    def test_piso_con_zocalo(self):
        r = _calc(superficie_m2=20, incluye_zocalo=True, perimetro_m=18)
        assert tiene_zocalo(r) is True

    def test_porcelanato_usa_adhesivo_flexible(self):
        r = _calc(superficie_m2=15, material="porcelanato_60x60")
        adh = next(p for p in r.partidas if "adhesivo" in p.concepto.lower())
        assert adh.cantidad == Decimal("5")

    def test_invariante_suma(self):
        r = _calc(superficie_m2=30)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(superficie_m2=20)
        for p in r.partidas:
            assert p.subtotal > 0


class TestValidacion:
    def test_zocalo_sin_perimetro_no_genera_partidas(self):
        r = _calc(superficie_m2=20, incluye_zocalo=True, perimetro_m=0)
        assert tiene_zocalo(r) is False


class TestPropiedades:
    @given(sup=st.floats(min_value=5.0, max_value=50.0))
    @settings(max_examples=10)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup)
        r2 = _calc(superficie_m2=sup)
        assert r1.total == r2.total