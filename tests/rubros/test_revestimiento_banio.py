"""Tests para src/rubros/revestimiento_banio.py"""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import src.rubros  # activa el registro
from src.rubros.revestimiento_banio import ParamsRevestimientoBanio
from src.rubros.base import REGISTRY

EMPRESA = "estudio_ramos"


def _calc(**kwargs):
    calc = REGISTRY["revestimiento_banio"]
    params = ParamsRevestimientoBanio(**kwargs)
    return calc.calcular(params, EMPRESA)


@pytest.fixture
def resultado_base():
    """Baño con distinto material piso/pared: porcelanato + cerámico."""
    return _calc(superficie_piso_m2=6, superficie_pared_m2=18)


class TestCasosBase:
    def test_banio_piso_y_paredes_distinto_material(self):
        r = _calc(
            superficie_piso_m2=6,
            superficie_pared_m2=18,
            material_piso="porcelanato_60x60",
            material_pared="ceramico_pared_25x35",
        )
        # Deben existir 2 partidas de MO separadas (piso y pared)
        mo_partidas = [p for p in r.partidas if p.categoria == "mano_obra"]
        assert len(mo_partidas) == 2

        # Material de piso: concepto "Piso material"
        mat_piso = next(p for p in r.partidas if p.concepto == "Piso material")
        # q(6 * 1.10) = 6.60
        assert mat_piso.cantidad == Decimal("6.60")

    def test_mismo_material_consolida_en_una_partida(self):
        r = _calc(
            superficie_piso_m2=6,
            superficie_pared_m2=18,
            material_piso="porcelanato_60x60",
            material_pared="porcelanato_60x60",
        )
        # El material de piso y pared debe consolidarse en "Piso y paredes material"
        consol = next(
            (p for p in r.partidas if p.concepto == "Piso y paredes material"), None
        )
        assert consol is not None, "Debe existir partida consolidada"
        # q(6*1.10) + q(18*1.10) = 6.60 + 19.80 = 26.40
        assert consol.cantidad == Decimal("26.40")

        # Las partidas separadas "Piso material" y "Pared material" no deben existir
        assert not any(p.concepto == "Piso material" for p in r.partidas)
        assert not any(p.concepto == "Pared material" for p in r.partidas)

    def test_cocina_con_alzada(self):
        r = _calc(
            superficie_piso_m2=6,
            superficie_pared_m2=18,
            material_piso="porcelanato_60x60",
            material_pared="ceramico_pared_25x35",
            incluye_alzada_cocina=True,
            superficie_alzada_m2=2.5,
        )
        # Con alzada, deben existir 3 partidas de MO (piso, pared, alzada)
        mo_partidas = [p for p in r.partidas if p.categoria == "mano_obra"]
        assert len(mo_partidas) == 3

        # Debe existir partida "Alzada material"
        alz_mat = next((p for p in r.partidas if p.concepto == "Alzada material"), None)
        assert alz_mat is not None

    def test_invariante_suma_partidas_igual_total(self, resultado_base):
        assert sum(p.subtotal for p in resultado_base.partidas) == resultado_base.total

    def test_partidas_tienen_subtotales_positivos(self, resultado_base):
        for p in resultado_base.partidas:
            assert p.subtotal > 0

    def test_metadata_completa(self, resultado_base):
        assert "superficie_piso_m2" in resultado_base.metadata
        assert "superficie_pared_m2" in resultado_base.metadata

    def test_solo_piso_funciona(self):
        r = _calc(superficie_piso_m2=10, superficie_pared_m2=0)
        assert r.total > 0

    def test_solo_pared_funciona(self):
        r = _calc(superficie_piso_m2=0, superficie_pared_m2=20)
        assert r.total > 0


class TestValidacion:
    def test_sin_superficie_falla(self):
        with pytest.raises(ValueError):
            _calc(superficie_piso_m2=0, superficie_pared_m2=0)

    def test_superficie_negativa_falla(self):
        with pytest.raises(Exception):
            _calc(superficie_piso_m2=-1, superficie_pared_m2=10)


class TestPropiedades:
    @given(sup_piso=st.floats(min_value=1.0, max_value=20.0),
           sup_pared=st.floats(min_value=1.0, max_value=40.0))
    @settings(max_examples=30)
    def test_idempotencia(self, sup_piso, sup_pared):
        r1 = _calc(superficie_piso_m2=sup_piso, superficie_pared_m2=sup_pared)
        r2 = _calc(superficie_piso_m2=sup_piso, superficie_pared_m2=sup_pared)
        assert r1.total == r2.total

    @given(sup=st.floats(min_value=1.0, max_value=39.0))
    @settings(max_examples=30)
    def test_mas_superficie_pared_mas_total(self, sup):
        r1 = _calc(superficie_piso_m2=6, superficie_pared_m2=sup)
        r2 = _calc(superficie_piso_m2=6, superficie_pared_m2=sup + 1.0)
        assert r2.total >= r1.total


class TestGolden:
    """Valores calculados manualmente con precios de precios_materiales.csv y precios_mano_obra.csv."""

    def test_golden_banio_001_distinto_material(self):
        # Piso: porcelanato_60x60, sup=6m2
        #   cant_mat=q(6*1.10)=6.60; cant_adh=ceil(6/3)=2; cant_junta=ceil(6/3)=2
        #   sub_piso_mat = 6.60*22500 + 2*12500 + 2*1800 = 148500+25000+3600 = 177100
        #   mo_piso = 6800*6 = 40800
        # Pared: ceramico_pared_25x35, sup=18m2
        #   cant_mat=q(18*1.10)=19.80; cant_adh=ceil(18/4)=5; cant_junta=ceil(18/3)=6
        #   sub_pared_mat = 19.80*14500 + 5*8500 + 6*1800 = 287100+42500+10800 = 340400
        #   mo_pared = 7800*18 = 140400
        # sub_mat = 177100 + 340400 = 517500
        # sub_mo  = 40800 + 140400 = 181200
        # total = 698700
        r = _calc(
            superficie_piso_m2=6,
            superficie_pared_m2=18,
            material_piso="porcelanato_60x60",
            material_pared="ceramico_pared_25x35",
        )
        assert r.total == Decimal("698700.00")

    def test_golden_banio_002_mismo_material(self):
        # Ambos porcelanato_60x60 → consolidación
        # Piso: q(6*1.10)=6.60; Pared: q(18*1.10)=19.80; consol=26.40
        # sub_consol = q(26.40*22500) = 594000
        # Adhesivos piso: ceil(6/3)=2 * 12500 = 25000; Junta piso: ceil(6/3)=2 * 1800 = 3600
        # Adhesivos pared: ceil(18/3)=6 * 12500 = 75000; Junta pared: ceil(18/3)=6 * 1800 = 10800
        # sub_mat = 594000+25000+3600+75000+10800 = 708400
        # mo_piso  = 6800*6  = 40800
        # mo_pared = 7800*18 = 140400
        # sub_mo = 181200; total = 889600
        r = _calc(
            superficie_piso_m2=6,
            superficie_pared_m2=18,
            material_piso="porcelanato_60x60",
            material_pared="porcelanato_60x60",
        )
        assert r.total == Decimal("889600.00")

    def test_golden_banio_003_cocina_con_alzada(self):
        # Piso: porc60, sup=6 → sub_mat=177100, mo=40800
        # Pared: cer25x35, sup=18 → sub_mat=340400, mo=140400
        # Alzada: cer25x35, sup=2.5
        #   cant_mat=q(2.5*1.10)=2.75; cant_adh=ceil(2.5/4)=1; cant_junta=ceil(2.5/3)=1
        #   sub_alz_mat = 2.75*14500 + 1*8500 + 1*1800 = 39875+8500+1800 = 50175
        #   mo_alz = 7800*2.5 = 19500
        # sub_mat = 177100+340400+50175 = 567675
        # sub_mo  = 40800+140400+19500 = 200700
        # total = 768375
        r = _calc(
            superficie_piso_m2=6,
            superficie_pared_m2=18,
            material_piso="porcelanato_60x60",
            material_pared="ceramico_pared_25x35",
            incluye_alzada_cocina=True,
            superficie_alzada_m2=2.5,
        )
        assert r.total == Decimal("768375.00")
