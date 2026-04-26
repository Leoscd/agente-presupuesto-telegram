"""Tests para actualizar precios y hot-reload."""
from __future__ import annotations

import os
import shutil
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
os.environ["DATA_DIR"] = str(ROOT / "empresas")

from src.datos.loader import (
    _cargar,
    actualizar_precio_material,
    actualizar_precio_mano_obra,
    cargar_empresa,
    _mtime_signature,
)


# Usar empresa real para tests
EMPRESA_TEST = "estudio_ramos"


@pytest.fixture
def empresa_con_datos():
    """Empresa temporal basada en estudio_ramos para tests, con backup."""
    # Backup de archivos originales
    src_dir = ROOT / "empresas" / EMPRESA_TEST
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        backup_dir = tmp_path / EMPRESA_TEST
        
        # Copiar solo los archivos que modificamos
        shutil.copy(src_dir / "precios_materiales.csv", tmp_path / "precios_materiales.csv")
        shutil.copy(src_dir / "precios_mano_obra.csv", tmp_path / "precios_mano_obra.csv")
        
        # Limpiar caché
        _cargar.cache_clear()
        
        yield EMPRESA_TEST
        
        # Restaurar
        shutil.copy(tmp_path / "precios_materiales.csv", src_dir / "precios_materiales.csv")
        shutil.copy(tmp_path / "precios_mano_obra.csv", src_dir / "precios_mano_obra.csv")
        _cargar.cache_clear()


class TestActualizarPrecioMaterial:
    def test_actualizar_precio_material_cambia_precio(self, empresa_con_datos):
        """Verify que actualizar_precio_material cambia el precio."""
        empresa_id = empresa_con_datos
        
        # Cargar precio original
        datos = cargar_empresa(empresa_id)
        df = datos.precios_materiales
        codigo = df.iloc[0]["codigo"]
        precio_original = Decimal(str(df.iloc[0]["precio"]))
        
        nuevo_precio = Decimal("999.99")
        
        # Actualizar
        precio_anterior = actualizar_precio_material(empresa_id, codigo, nuevo_precio)
        
        assert precio_anterior == precio_original
        
        # Verificar cambio (recargando)
        datos_nuevo = cargar_empresa(empresa_id)
        df_nuevo = datos_nuevo.precios_materiales
        precio_nuevo = Decimal(str(df_nuevo.loc[
            df_nuevo["codigo"] == codigo, "precio"
        ].iloc[0]))
        
        assert precio_nuevo == nuevo_precio

    def test_actualizar_precio_material_codigo_inexistente(self, empresa_con_datos):
        """actualizar_precio_material con código inexistente debe levantar exception."""
        from src.datos.loader import MaterialNoEncontrado
        
        with pytest.raises(MaterialNoEncontrado):
            actualizar_precio_material(empresa_con_datos, "CODIGO_INEXISTENTE_XXX", Decimal("100"))


class TestActualizarPrecioManoObra:
    def test_actualizar_precio_mano_obra_cambia_precio(self, empresa_con_datos):
        """Verify que actualizar_precio_mano_obra cambia el precio."""
        empresa_id = empresa_con_datos
        
        # Cargar precio original
        datos = cargar_empresa(empresa_id)
        df = datos.precios_mano_obra
        tarea = df.iloc[0]["tarea"]
        precio_original = Decimal(str(df.iloc[0]["precio"]))
        
        nuevo_precio = Decimal("555.55")
        
        # Actualizar
        precio_anterior = actualizar_precio_mano_obra(empresa_id, tarea, nuevo_precio)
        
        assert precio_anterior == precio_original
        
        # Verificar cambio (recargando)
        datos_nuevo = cargar_empresa(empresa_id)
        df_nuevo = datos_nuevo.precios_mano_obra
        precio_nuevo = Decimal(str(df_nuevo.loc[
            df_nuevo["tarea"] == tarea, "precio"
        ].iloc[0]))
        
        assert precio_nuevo == nuevo_precio

    def test_actualizar_precio_mano_obra_inexistente(self, empresa_con_datos):
        """actualizar_precio_mano_obra con tarea inexistente debe levantar exception."""
        from src.datos.loader import MaterialNoEncontrado
        
        with pytest.raises(MaterialNoEncontrado):
            actualizar_precio_mano_obra(empresa_con_datos, "TAREA_INEXISTENTE_XXX", Decimal("100"))


class TestHotReload:
    def test_hot_reload_actualiza_mtime(self, empresa_con_datos):
        """Verify que el mtime cambia después de actualizar precio."""
        import time
        from src.datos.loader import _mtime_signature
        
        empresa_id = empresa_con_datos
        
        # Obtener signature original
        sig_original = _mtime_signature(empresa_id)
        
        # Actualizar precio
        datos = cargar_empresa(empresa_id)
        codigo = datos.precios_materiales.iloc[0]["codigo"]
        actualizar_precio_material(empresa_id, codigo, Decimal("123.45"))
        
        # small delay para asegurar mtime diferente
        time.sleep(0.1)
        
        # Nueva signature debe ser diferente
        sig_nueva = _mtime_signature(empresa_id)
        
        # Al menos un archivo debe tener mtime diferente
        assert sig_nueva != sig_original