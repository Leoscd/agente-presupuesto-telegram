"""Tests para memoria de sesión conversacional (Tarea 16)."""
import pytest
from unittest.mock import patch, MagicMock
import json

from src.persistencia import db


class TestSesionesDB:
    """Tests para funciones de sesión en db.py."""

    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path, monkeypatch):
        # Crear DB temporal
        from src.config import settings
        settings.db_path = tmp_path / "test.db"
        db.init_db()

    def test_guardar_sesion_y_obtener(self):
        """Guardar y obtener sesión funciona."""
        db.guardar_sesion(
            telegram_user_id=123,
            empresa_id="estudio_ramos",
            accion="techo_chapa",
            params={"ancho": 7, "largo": 10},
            resultado_id=None,
        )

        sesion = db.obtener_sesion(123)
        assert sesion is not None
        assert sesion["accion"] == "techo_chapa"
        assert sesion["params"]["ancho"] == 7

    def test_obtener_sesion_inexistente(self):
        """Obtener sesión inexistente devuelve None."""
        sesion = db.obtener_sesion(999)
        assert sesion is None

    def test_limpiar_sesion(self):
        """Limpiar sesión borra los datos."""
        db.guardar_sesion(
            telegram_user_id=456,
            empresa_id="estudio_ramos",
            accion="mamposteria",
            params={"largo": 5, "alto": 3},
            resultado_id=None,
        )

        db.limpiar_sesion(456)
        sesion = db.obtener_sesion(456)
        assert sesion is None

    def test_actualizar_sesion_existente(self):
        """Actualizar sesión sobrescribe la anterior."""
        db.guardar_sesion(
            telegram_user_id=789,
            empresa_id="estudio_ramos",
            accion="losa",
            params={"ancho": 4, "largo": 5},
            resultado_id=None,
        )

        # Actualizar con nuevos params
        db.guardar_sesion(
            telegram_user_id=789,
            empresa_id="estudio_ramos",
            accion="losa",
            params={"ancho": 6, "largo": 8},
            resultado_id=None,
        )

        sesion = db.obtener_sesion(789)
        assert sesion["params"]["ancho"] == 6
        assert sesion["params"]["largo"] == 8