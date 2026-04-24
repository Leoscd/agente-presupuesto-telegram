"""Tests para src/rubros/revoque_grueso.py"""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import src.rubros  # activa el registro
from src.rubros.revoque_grueso import ParamsRevoqueGrueso
from src.rubros.base import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    calc = REGISTRY["revoque_grueso"]
    params = ParamsRevoqueGrueso(**kwargs)
    return calc.calcular(params, EMPRESA)


@pytest.fixture
def resultado_base():
    return _calc(superficie_m2=30, espesor_cm=1.5)


class TestCasosBase:
    def test_revoque_30m2(self, resultado_base):
        r = resultado_base
        assert r.metadata["superficie_m2"] == 30.0
        # m3 = 30 * 1.5 / 100 = 0.45
        assert r.metadata["volumen_mortero_m3"] == pytest.approx(0.45, abs=0.001)

        cemento = next(p for p in r.partidas if "cemento" in p.concepto.lower())
        # ceil(0.45 / 0.035) = ceil(12.857) = 13
        assert cemento.cantidad == Decimal("13")

    def test_plastificante_minimo(self):
        """Con superficie_m2=10, el plastificante debe ser mínimo 1."""
        r = _calc(superficie_m2=10, espesor_cm=1.5)
        plast = next(p for p in r.partidas if "plastificante" in p.concepto.lower())
        # ceil(10/30) = 1 — pero max(1, ...) garantiza el mínimo
        assert plast.cantidad == Decimal("1")

    def test_invariante_suma_partidas_igual_total(self, resultado_base):
        assert sum(p.subtotal for p in resultado_base.partidas) == resultado_base.total

    def test_partidas_tienen_subtotales_positivos(self, resultado_base):
        for p in resultado_base.partidas:
            assert p.subtotal > 0

    def test_metadata_completa(self, resultado_base):
        assert "superficie_m2" in resultado_base.metadata
        assert "volumen_mortero_m3" in resultado_base.metadata

    def test_partidas_esperadas(self, resultado_base):
        conceptos = [p.concepto.lower() for p in resultado_base.partidas]
        assert any("cemento" in c for c in conceptos)
        assert any("arena" in c for c in conceptos)
        assert any("plastificante" in c for c in conceptos)
        mo_partidas = [p for p in resultado_base.partidas if p.categoria == "mano_obra"]
        assert len(mo_partidas) == 1


class TestValidacion:
    @pytest.mark.parametrize("espesor", [0.4, 3.1, 0, -1])
    def test_espesor_fuera_de_rango_falla(self, espesor):
        with pytest.raises(Exception):
            _calc(superficie_m2=30, espesor_cm=espesor)

    def test_superficie_negativa_falla(self):
        with pytest.raises(Exception):
            _calc(superficie_m2=-5, espesor_cm=1.5)

    def test_superficie_cero_falla(self):
        with pytest.raises(Exception):
            _calc(superficie_m2=0, espesor_cm=1.5)


class TestPropiedades:
    @given(sup=st.floats(min_value=5.0, max_value=100.0))
    @settings(max_examples=30)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup, espesor_cm=1.5)
        r2 = _calc(superficie_m2=sup, espesor_cm=1.5)
        assert r1.total == r2.total

    @given(sup=st.floats(min_value=5.0, max_value=99.0))
    @settings(max_examples=30)
    def test_mas_superficie_mas_total(self, sup):
        r1 = _calc(superficie_m2=sup, espesor_cm=1.5)
        r2 = _calc(superficie_m2=sup + 1.0, espesor_cm=1.5)
        assert r2.total >= r1.total


class TestGolden:
    """Valores calculados manualmente con precios de precios_materiales.csv y precios_mano_obra.csv."""

    def test_golden_revg_001_30m2_esp1_5(self):
        # m3 = 30 * 1.5 / 100 = 0.450
        # cemento=ceil(0.450/0.035)=ceil(12.857)=13; arena=0.450*3=1.35
        # plast=max(1, ceil(30/30))=1
        # sub_mat = 13*12500 + 1.35*38000 + 1*18500
        #         = 162500 + 51300 + 18500 = 232300
        # sub_mo = 3200*30 = 96000; total = 328300
        r = _calc(superficie_m2=30, espesor_cm=1.5)
        assert r.total == Decimal("328300.00")

    def test_golden_revg_002_60m2_esp2_0(self):
        # m3 = 60 * 2.0 / 100 = 1.200
        # cemento=ceil(1.200/0.035)=ceil(34.286)=35; arena=1.200*3=3.60
        # plast=max(1, ceil(60/30))=2
        # sub_mat = 35*12500 + 3.60*38000 + 2*18500
        #         = 437500 + 136800 + 37000 = 611300
        # sub_mo = 3200*60 = 192000; total = 803300
        r = _calc(superficie_m2=60, espesor_cm=2.0)
        assert r.total == Decimal("803300.00")
