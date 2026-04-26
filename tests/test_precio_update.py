"""Tests para actualizacion de precios por lenguaje natural."""
from decimal import Decimal
import pytest
from src.datos.loader import (
    actualizar_precio_material,
    actualizar_precio_mano_obra,
    MaterialNoEncontrado,
    cargar_empresa,
)

EMPRESA_TEST = "estudio_ramos"


class TestActualizarPrecioMaterial:
    def test_actualizar_precio_material_codigo_inexistente(self):
        """ codigo inexistente debe levantar exception """
        with pytest.raises(MaterialNoEncontrado, match="no encontrado"):
            actualizar_precio_material(EMPRESA_TEST, "MATERIAL_INVENTADO_XYZ", Decimal("1000"))

    def test_actualizar_precio_material_por_descripcion(self):
        """ buscar por descripcion (case-insensitive) """
        # Cemento debe existir
        datos = cargar_empresa(EMPRESA_TEST)
        precio_antes = datos.precios_materiales[datos.precios_materiales["codigo"] == "CEMENTO_PORTLAND"].iloc[0]["precio"]
        
        # Actualizar via descripcion
        precio_nuevo = Decimal("7500.00")
        actualizar_precio_material(EMPRESA_TEST, "cemento portland", precio_nuevo)
        
        # Verificar cambio
        datos = cargar_empresa(EMPRESA_TEST)  # Recarga por mtime
        precio_despues = datos.precios_materiales[datos.precios_materiales["codigo"] == "CEMENTO_PORTLAND"].iloc[0]["precio"]
        
        # Restaurar precio original
        actualizar_precio_material(EMPRESA_TEST, "CEMENTO_PORTLAND", Decimal(str(precio_antes)))
        
        assert precio_despues == 7500.00


class TestActualizarPrecioManoObra:
    def test_actualizar_precio_mano_obra_codigo_inexistente(self):
        """ tarea inexistente debe levantar exception """
        with pytest.raises(MaterialNoEncontrado, match="no encontrada"):
            actualizar_precio_mano_obra(EMPRESA_TEST, "TAREA_INVENTADA_XYZ", Decimal("1000"))

    def test_actualizar_precio_mano_obra_existente(self):
        """ actualizar tarea existente """
        datos = cargar_empresa(EMPRESA_TEST)
        tarea_row = datos.precios_mano_obra[datos.precios_mano_obra["tarea"] == "PINTURA"]
        if tarea_row.empty:
            pytest.skip("Tarea PINTURA no existe en empresa test")
        
        precio_antes = tarea_row.iloc[0]["precio"]
        precio_nuevo = Decimal("4000.00")
        
        actualizar_precio_mano_obra(EMPRESA_TEST, "PINTURA", precio_nuevo)
        
        # Verificar
        datos = cargar_empresa(EMPRESA_TEST)
        precio_despues = datos.precios_mano_obra[datos.precios_mano_obra["tarea"] == "PINTURA"].iloc[0]["precio"]
        
        # Restaurar
        actualizar_precio_mano_obra(EMPRESA_TEST, "PINTURA", Decimal(str(precio_antes)))
        
        assert precio_despues == 4000.00


class TestListar:
    def test_listar_materiales_con_descripcion(self):
        from src.datos.loader import listar_materiales_con_descripcion
        mats = listar_materiales_con_descripcion(EMPRESA_TEST)
        assert len(mats) > 0
        assert "codigo" in mats[0]
        assert "precio_actual" in mats[0]

    def test_listar_mo_con_descripcion(self):
        from src.datos.loader import listar_mo_con_descripcion
        mos = listar_mo_con_descripcion(EMPRESA_TEST)
        assert len(mos) > 0
        assert "tarea" in mos[0]
        assert "precio_actual" in mos[0]
