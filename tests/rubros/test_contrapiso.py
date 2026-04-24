"""Tests para src/rubros/contrapiso.py"""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import src.rubros  # activa el registro
from src.rubros.contrapiso import ParamsContrapiso
from src.rubros.base import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    calc = REGISTRY["contrapiso"]
    params = ParamsContrapiso(**kwargs)
    return calc.calcular(params, EMPRESA)


@pytest.fixture
def resultado_base():
    return _calc(superficie_m2=20, espesor_cm=8)


class TestCasosBase:
    def test_contrapiso_20m2_esp8(self, resultado_base):
        r = resultado_base
        assert r.metadata["superficie_m2"] == 20.0
        # m3 = 20 * 8 / 100 = 1.60
        assert r.metadata["volumen_m3"] == pytest.approx(1.60, abs=0.01)

        cemento = next(p for p in r.partidas if "cemento" in p.concepto.lower())
        # ceil(1.60 * 4) = 7
        assert cemento.cantidad == Decimal("7")

    def test_invariante_suma_partidas_igual_total(self, resultado_base):
        assert sum(p.subtotal for p in resultado_base.partidas) == resultado_base.total

    def test_partidas_tienen_subtotales_positivos(self, resultado_base):
        for p in resultado_base.partidas:
            assert p.subtotal > 0

    def test_metadata_completa(self, resultado_base):
        assert "superficie_m2" in resultado_base.metadata
        assert "volumen_m3" in resultado_base.metadata

    def test_partidas_esperadas(self, resultado_base):
        conceptos = [p.concepto.lower() for p in resultado_base.partidas]
        assert any("cemento" in c for c in conceptos)
        assert any("arena" in c for c in conceptos)
        assert any("piedra" in c for c in conceptos)
        assert any("mo" in c or "contrapiso" in c for c in conceptos)


class TestValidacion:
    @pytest.mark.parametrize("espesor", [4.9, 15.1, 0, -1])
    def test_espesor_fuera_de_rango_falla(self, espesor):
        with pytest.raises(Exception):
            _calc(superficie_m2=20, espesor_cm=espesor)

    def test_superficie_negativa_falla(self):
        with pytest.raises(Exception):
            _calc(superficie_m2=-1, espesor_cm=8)

    def test_superficie_cero_falla(self):
        with pytest.raises(Exception):
            _calc(superficie_m2=0, espesor_cm=8)


class TestPropiedades:
    @given(sup=st.floats(min_value=5.0, max_value=100.0))
    @settings(max_examples=30)
    def test_idempotencia(self, sup):
        r1 = _calc(superficie_m2=sup, espesor_cm=8)
        r2 = _calc(superficie_m2=sup, espesor_cm=8)
        assert r1.total == r2.total

    @given(sup=st.floats(min_value=5.0, max_value=99.0))
    @settings(max_examples=30)
    def test_mas_superficie_mas_total(self, sup):
        r1 = _calc(superficie_m2=sup, espesor_cm=8)
        r2 = _calc(superficie_m2=sup + 1.0, espesor_cm=8)
        assert r2.total >= r1.total


class TestGolden:
    """Valores calculados manualmente con precios de precios_materiales.csv y precios_mano_obra.csv."""

    def test_golden_cont_001_20m2_esp8(self):
        # m3 = 20 * 8 / 100 = 1.60
        # cemento=ceil(1.60*4)=7; arena=1.60*0.55=0.88; piedra=1.60*0.65=1.04
        # sub_mat = 7*12500 + 0.88*38000 + 1.04*45000
        #         = 87500 + 33440 + 46800 = 167740
        # sub_mo = 4500*20 = 90000; total = 257740
        r = _calc(superficie_m2=20, espesor_cm=8)
        assert r.total == Decimal("257740.00")

    def test_golden_cont_002_50m2_esp10(self):
        # m3 = 50 * 10 / 100 = 5.00
        # cemento=ceil(5.00*4)=20; arena=5.00*0.55=2.75; piedra=5.00*0.65=3.25
        # sub_mat = 20*12500 + 2.75*38000 + 3.25*45000
        #         = 250000 + 104500 + 146250 = 500750
        # sub_mo = 4500*50 = 225000; total = 725750
        r = _calc(superficie_m2=50, espesor_cm=10)
        assert r.total == Decimal("725750.00")
