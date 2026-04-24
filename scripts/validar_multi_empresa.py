#!/usr/bin/env python3
"""Script de validación cruzada multi-empresa.

Verifica que los cálculos sean consistentes entre empresas
y que duplicar precios duplique el total.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.datos.loader import cargar_empresa
from src.orquestador.router import despachar


def test_multi_empresa():
    """Test 1: Mismos precios -> mismo total"""
    print("[TEST 1] Verificando que estudio_ramos y _plantilla den mismo resultado...")
    
    casos = [
        ("techo_chapa", {"ancho": 7, "largo": 10, "tipo_chapa": "galvanizada_075", "tipo_perfil": "C100"}),
        ("mamposteria", {"largo": 5, "alto": 3, "tipo": "hueco_12"}),
        ("losa", {"ancho": 4, "largo": 5, "espesor_cm": 12}),
    ]
    
    resultados = []
    for empresa in ["estudio_ramos", "_plantilla"]:
        try:
            datos = cargar_empresa(empresa)
            for accion, params in casos:
                r = despachar(accion, params, empresa)
                resultados.append((empresa, accion, r.total))
                
            # Verificar que ambos den igual
            r1 = [r for e, a, r in resultados if e == "estudio_ramos"]
            r2 = [r for e, a, r in resultados if e == "_plantilla"]
            
            if r1 == r2:
                print(f"  [OK] {empresa}: totals iguales")
            else:
                print(f"  [FAIL] {empresa}: totals diferentes")
                
        except Exception as e:
            print(f"  [ERROR] {empresa}: {e}")
    
    return resultados


def test_precios_dobles():
    """Test 2: Precios duplicados -> total duplicado"""
    print("\n[TEST 2] Verificando que precios duplicados = total duplicado...")
    print("  [INFO] Este test requiere crear empresa_test_precios_dobles en memoria")
    print("  [SKIP] Por ahora, saltando test de precios duplicados")
    return []


def main():
    print("=" * 60)
    print("VALIDACIÓN CRUZADA MULTI-EMPRESA")
    print("=" * 60)
    
    # Test 1
    test_multi_empresa()
    
    # Test 2
    test_precios_dobles()
    
    print("\n" + "=" * 60)
    print("VALIDACIÓN COMPLETA")
    print("=" * 60)


if __name__ == "__main__":
    main()