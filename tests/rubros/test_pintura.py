"""Tests para src/rubros/pintura.py"""
from __future__ import annotations
from decimal import Decimal
from math import ceil
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.rubros.pintura import ParamsPintura, RENDIMIENTO_L_M2, LITROS_POR_BALDE
from src.rubros import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    return REGISTRY["pintura"].calcular(ParamsPintura(**kwargs), EMPRESA)


class TestCasosBase:
    def test_latex_interior(self):
        r = _calc(superficie_m2=50.0, tipo="latex_interior", manos=2)
        assert r.total > 0

    def test_latex_exterior(self):
        r = _calc(superficie_m2=50.0, tipo="latex_exterior", manos=2)
        assert r.total > 0

    def test_esmalte_sintetico(self):
        r = _calc(superficie_m2=20.0, tipo="esmalte_sintetico", manos=2)
        assert r.total > 0

    def test_invariante_suma(self):
        r = _calc(superficie_m2=50.0, tipo="latex_interior", manos=2)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(superficie_m2=50.0, tipo="latex_interior", manos=2)
        for p in r.partidas:
            assert p.subtotal > 0

    def test_baldes_latex_interior_60m2_2manos(self):
        # litros = 60 * 2 / 12 = 10L → ceil(10/20) = 1 balde
        r = _calc(superficie_m2=60.0, tipo="latex_interior", manos=2, incluye_fijador=False)
        balde_partida = next(p for p in r.partidas if "Pintura" in p.concepto)
        assert balde_partida.cantidad == Decimal("1")

    def test_baldes_latex_interior_120m2_2manos(self):
        # litros = 120 * 2 / 12 = 20L → ceil(20/20) = 1 balde
        r = _calc(superficie_m2=120.0, tipo="latex_interior", manos=2, incluye_fijador=False)
        balde_partida = next(p for p in r.partidas if "Pintura" in p.concepto)
        assert balde_partida.cantidad == Decimal("1")

    def test_baldes_latex_interior_121m2_2manos(self):
        # litros = 121 * 2 / 12 = 20.17L → ceil(20.17/20) = 2 baldes
        r = _calc(superficie_m2=121.0, tipo="latex_interior", manos=2, incluye_fijador=False)
        balde_partida = next(p for p in r.partidas if "Pintura" in p.concepto)
        assert balde_partida.cantidad == Decimal("2")

    def test_baldes_esmalte_pequeno(self):
        # 20m2, 1 mano: litros = 20*1/12 = 1.67L → ceil(1.67/4) = 1 balde 4L
        r = _calc(superficie_m2=20.0, tipo="esmalte_sintetico", manos=1, incluye_fijador=False)
        balde_partida = next(p for p in r.partidas if "Pintura" in p.concepto)
        assert balde_partida.cantidad == Decimal("1")

    def test_fijador_incluido_por_defecto(self):
        # incluye_fijador=True by default → debe haber partida de fijador
        r = _calc(superficie_m2=50.0, tipo="latex_interior", manos=2)
        conceptos = [p.concepto for p in r.partidas]
        assert any("Fijador" in c for c in conceptos)

    def test_sin_fijador(self):
        r = _calc(superficie_m2=50.0, tipo="latex_interior", manos=2, incluye_fijador=False)
        conceptos = [p.concepto for p in r.partidas]
        assert not any("Fijador" in c for c in conceptos)

    def test_lija_cant_correcta(self):
        # 50m2 → ceil(50/10) = 5 pliegos
        r = _calc(superficie_m2=50.0, tipo="latex_interior", manos=2, incluye_fijador=False)
        lija = next(p for p in r.partidas if "Lija" in p.concepto)
        assert lija.cantidad == Decimal("5")

    def test_metadata_completa(self):
        r = _calc(superficie_m2=50.0, tipo="latex_interior", manos=2)
        assert "superficie_m2" in r.metadata
        assert "tipo" in r.metadata
        assert "manos" in r.metadata
        assert "incluye_fijador" in r.metadata


class TestPropiedades:
    @given(sup=st.floats(min_value=5.0, max_value=200.0))
    @settings(max_examples=10)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup, tipo="latex_interior", manos=2)
        r2 = _calc(superficie_m2=sup, tipo="latex_interior", manos=2)
        assert r1.total == r2.total

    @given(sup=st.floats(min_value=5.0, max_value=200.0))
    @settings(max_examples=10)
    def test_invariante_suma_property(self, sup):
        r = _calc(superficie_m2=sup, tipo="latex_interior", manos=2)
        assert sum(p.subtotal for p in r.partidas) == r.total