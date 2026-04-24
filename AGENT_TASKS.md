# ESTADO DE TAREA - Fase 3 (continuación)

## ✅ COMPLETADO

- Fase 2 completa: mamposteria, losa, contrapiso, revoque_grueso, cubierta_tejas, revestimiento_banio
- Two-stage routing MiniMax
- instalacion_electrica, instalacion_sanitaria, revoque_fino (implementados anticipadamente)
- Tests: 108 passing
- Golden cases: 18 casos

## ⚠️ PENDIENTE

- Tarea 1: Rubro `piso_ceramico` (no está en el registry todavía)
- Tarea 2: Actualizar `categorias.py`, `__init__.py` y `prompts.py`
- Tarea 3: Tests y golden cases faltantes (revoque_fino, instalacion_sanitaria, instalacion_electrica)
- Tarea 4: Tests y golden cases para `piso_ceramico`
- Tarea 5: Verificación final

---

# Tareas para el agente de código — Fase 3 cierre

> **Antes de empezar:** `git pull && python3 -m pytest tests/ -q`
> Deben pasar 108 tests. Si alguno falla, detener y reportar.
>
> El patrón de implementación está en `src/rubros/techo_chapa.py`.
> No modificar rubros existentes salvo lo indicado aquí.

---

## TAREA 1 — Rubro: Piso cerámico / porcelanato (standalone)

Este rubro cubre **solo piso** sin paredes. Aplica a living, cocina, locales.
Es distinto de `revestimiento_banio` que maneja piso + paredes juntos.

### Archivo: `src/rubros/piso_ceramico.py`

**Clase `ParamsPisoCeramico(BaseModel)`:**
```python
superficie_m2: PositiveFloat
material: Literal[
    "ceramico_30x30", "ceramico_45x45",
    "porcelanato_60x60", "porcelanato_60x60_premium"
] = "ceramico_45x45"
incluye_zocalo: bool = False
perimetro_m: float = Field(0.0, ge=0.0)
```

**Constantes:**
```python
CODIGO_MATERIAL = {
    "ceramico_30x30":            "CERAMICO_30X30",
    "ceramico_45x45":            "CERAMICO_45X45",
    "porcelanato_60x60":         "PORCELANATO_60X60",
    "porcelanato_60x60_premium": "PORCELANATO_60X60_PREMIUM",
}
CODIGO_ADHESIVO = {
    "ceramico_30x30":            "ADHESIVO_CERAMICO",
    "ceramico_45x45":            "ADHESIVO_CERAMICO",
    "porcelanato_60x60":         "ADHESIVO_PORCELANATO",
    "porcelanato_60x60_premium": "ADHESIVO_PORCELANATO",
}
ADHESIVO_M2_POR_BOLSA = Decimal("4")
ADHESIVO_PORC_M2_POR_BOLSA = Decimal("3")
JUNTA_M2_POR_KG = Decimal("3")
```

**Agregar al CSV (ambas empresas + plantilla) si no existe:**
```
ZOCALO_CERAMICO,Zócalo cerámico 8x33cm,ml,3200.00,2026-04-24
```
Agregar `"ZOCALO_CERAMICO"` a `materiales_disponibles.json`.

Verificar que `PISO_CERAMICO` existe en `precios_mano_obra.csv` — fue agregado en Fase 2.

**⚠️ IMPORTANTE al modificar CSV:** Siempre verificar después con:
```bash
python3 -c "import pandas as pd; pd.read_csv('empresas/estudio_ramos/precios_materiales.csv'); print('OK')"
```
Si lanza `ParserError`, hay una línea concatenada sin salto de línea — corregirla antes de continuar.

**Fórmulas en `calcular()`:**
```python
sup = Decimal(str(params.superficie_m2))
es_porc = "porcelanato" in params.material
m2_por_bolsa = ADHESIVO_PORC_M2_POR_BOLSA if es_porc else ADHESIVO_M2_POR_BOLSA

cant_mat = _q(sup * rendimiento(datos, CODIGO_MATERIAL[params.material], Decimal("1.10")))
cant_adhesivo = Decimal(ceil(sup / m2_por_bolsa))
cant_junta = Decimal(ceil(sup / JUNTA_M2_POR_KG))
p_mo = precio_mano_obra(datos, "PISO_CERAMICO")
costo_mo = _q(p_mo * sup)

# Zócalo (solo si aplica)
if params.incluye_zocalo and params.perimetro_m > 0:
    perim = Decimal(str(params.perimetro_m))
    cant_zocalo = _q(perim * rendimiento(datos, "ZOCALO_CERAMICO", Decimal("1.05")))
    costo_mo_zoc = _q(p_mo * perim * Decimal("0.3"))
```

**Partidas (en este orden):**
1. Material de piso (m2, material)
2. Adhesivo (u, material)
3. Pastina/junta (kg, material)
4. Zócalo cerámico (ml, material) — solo si `incluye_zocalo and perimetro_m > 0`
5. MO colocación piso (m2, mano_obra)
6. MO zócalo (ml, mano_obra) — solo si `incluye_zocalo and perimetro_m > 0`

**`metadata`:** `superficie_m2`, `material`, `incluye_zocalo`, `perimetro_m`

`accion = "piso_ceramico"`. Llamar `registrar(...)` al final.

---

## TAREA 2 — Actualizar categorias.py, __init__.py y prompts.py

### `src/rubros/categorias.py`

Reemplazar:
```python
"instalaciones": [],  # fase 3
```
Por:
```python
"instalaciones": ["instalacion_electrica", "instalacion_sanitaria"],
```

Verificar que `terminaciones` ya incluye `piso_ceramico` (si no, agregarlo):
```python
"terminaciones": ["revoque_grueso", "revoque_fino", "piso_ceramico", "revestimiento_banio"],
```

### `src/rubros/__init__.py`

Agregar `piso_ceramico` a los imports (mantener los demás tal cual):
```python
from src.rubros import (  # noqa: F401
    ...
    piso_ceramico,
)
```

### `src/orquestador/prompts.py` — `SYSTEM_PROMPT`

Verificar cuáles rubros faltan en la sección "Acciones disponibles" y agregar los que no estén:

```
9. "revoque_fino":
   - superficie_m2: float
   - espesor_cm: float (default 0.5)

10. "piso_ceramico":
    - superficie_m2: float
    - material: "ceramico_30x30" | "ceramico_45x45" | "porcelanato_60x60" | "porcelanato_60x60_premium"
    - incluye_zocalo: bool (default false)
    - perimetro_m: float (default 0)

11. "instalacion_electrica":
    - superficie_m2: float
    - tipo: "basica" | "completa" (default "basica")
    - incluye_tablero: bool (default true)

12. "instalacion_sanitaria":
    - [ver ParamsInstalacionSanitaria en src/rubros/instalacion_sanitaria.py]
```

---

## TAREA 3 — Tests y golden cases faltantes

### `tests/rubros/test_revoque_fino.py` (archivo nuevo)

```python
"""Tests para src/rubros/revoque_fino.py"""
from __future__ import annotations
from decimal import Decimal
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
import src.rubros
from src.rubros.revoque_fino import ParamsRevoqueFino
from src.rubros.base import REGISTRY

EMPRESA = "estudio_ramos"

def _calc(**kwargs):
    return REGISTRY["revoque_fino"].calcular(ParamsRevoqueFino(**kwargs), EMPRESA)

class TestCasosBase:
    def test_caso_base(self):
        r = _calc(superficie_m2=20, espesor_cm=0.5)
        assert r.metadata["superficie_m2"] == 20.0
        assert r.total > 0

    def test_plastificante_minimo(self):
        r = _calc(superficie_m2=10)
        plast = next(p for p in r.partidas if "plastificante" in p.concepto.lower())
        assert plast.cantidad >= Decimal("1")

    def test_invariante_suma_igual_total(self):
        r = _calc(superficie_m2=30)
        assert sum(p.subtotal for p in r.partidas) == r.total

    def test_partidas_positivas(self):
        r = _calc(superficie_m2=20)
        for p in r.partidas:
            assert p.subtotal > 0

class TestValidacion:
    def test_espesor_fuera_de_rango_falla(self):
        with pytest.raises(Exception):
            _calc(superficie_m2=20, espesor_cm=5.0)

class TestPropiedades:
    @given(sup=st.floats(min_value=1.0, max_value=100.0))
    @settings(max_examples=30)
    def test_idempotencia(self, sup):
        assert _calc(superficie_m2=sup).total == _calc(superficie_m2=sup).total
```

### `tests/rubros/test_instalacion_sanitaria.py` (archivo nuevo)

Leer `src/rubros/instalacion_sanitaria.py` para entender los parámetros.
Seguir el mismo patrón: caso base, invariante suma, partidas positivas, validación, idempotencia.

### Golden cases — agregar al final de `tests/golden/casos.yaml`

Calcular los valores manualmente con los precios de `empresas/estudio_ramos/precios_materiales.csv` y `precios_mano_obra.csv`. **No correr el código para obtener los totales.**

Agregar estos 4 casos:

```yaml
- id: revf_001
  descripcion: "Revoque fino 20m2 espesor 0.5cm"
  accion: revoque_fino
  empresa_id: estudio_ramos
  parametros:
    superficie_m2: 20
    espesor_cm: 0.5
  esperado:
    total: "CALCULAR_MANUALMENTE"
    subtotal_materiales: "CALCULAR_MANUALMENTE"
    subtotal_mano_obra: "CALCULAR_MANUALMENTE"

- id: revf_002
  descripcion: "Revoque fino 50m2 espesor 1.0cm"
  accion: revoque_fino
  empresa_id: estudio_ramos
  parametros:
    superficie_m2: 50
    espesor_cm: 1.0
  esperado:
    total: "CALCULAR_MANUALMENTE"
    subtotal_materiales: "CALCULAR_MANUALMENTE"
    subtotal_mano_obra: "CALCULAR_MANUALMENTE"

- id: elec_001
  descripcion: "Instalación eléctrica básica 50m2 con tablero"
  accion: instalacion_electrica
  empresa_id: estudio_ramos
  parametros:
    superficie_m2: 50
    tipo: "basica"
    incluye_tablero: true
  esperado:
    total: "CALCULAR_MANUALMENTE"
    subtotal_materiales: "CALCULAR_MANUALMENTE"
    subtotal_mano_obra: "CALCULAR_MANUALMENTE"

- id: san_001
  descripcion: "[completar según parámetros de instalacion_sanitaria]"
  accion: instalacion_sanitaria
  empresa_id: estudio_ramos
  parametros: {}
  esperado:
    total: "CALCULAR_MANUALMENTE"
    subtotal_materiales: "CALCULAR_MANUALMENTE"
    subtotal_mano_obra: "CALCULAR_MANUALMENTE"
```

---

## TAREA 4 — Tests para piso_ceramico

### `tests/rubros/test_piso_ceramico.py` (archivo nuevo, crear después de Tarea 1)

```python
class TestCasosBase:
    def test_piso_sin_zocalo(self):
        r = _calc(superficie_m2=20, material="ceramico_45x45")
        assert not any("zocalo" in p.concepto.lower() for p in r.partidas)

    def test_piso_con_zocalo(self):
        r = _calc(superficie_m2=20, incluye_zocalo=True, perimetro_m=18)
        assert any("zocalo" in p.concepto.lower() for p in r.partidas)

    def test_porcelanato_usa_adhesivo_flexible(self):
        r = _calc(superficie_m2=15, material="porcelanato_60x60")
        adh = next(p for p in r.partidas if "adhesivo" in p.concepto.lower())
        # porcelanato: ceil(15/3) = 5
        assert adh.cantidad == Decimal("5")

    def test_invariante_suma_igual_total(self): ...
    def test_partidas_positivas(self): ...

class TestValidacion:
    def test_zocalo_sin_perimetro_no_genera_partidas(self):
        r = _calc(superficie_m2=20, incluye_zocalo=True, perimetro_m=0)
        assert not any("zocalo" in p.concepto.lower() for p in r.partidas)

class TestPropiedades:
    # idempotencia con hypothesis
```

3 golden cases: ceramico_45x45 20m2, porcelanato_60x60 15m2, ceramico_30x30 30m2 con zócalo 20ml.

---

## TAREA 5 — Verificación final

```bash
git pull
python3 -m pytest tests/ -q
# Esperado: >= 130 passed, 0 failed

python3 -c "
import src.rubros
from src.rubros.base import REGISTRY
from src.rubros.categorias import CATEGORIAS
print('Registry:', list(REGISTRY.keys()))
print('instalaciones:', CATEGORIAS['instalaciones'])
print('terminaciones:', CATEGORIAS['terminaciones'])
"
# Registry debe incluir piso_ceramico
# instalaciones: ['instalacion_electrica', 'instalacion_sanitaria']
# terminaciones: incluye piso_ceramico
```

Commit al terminar:
```
feat: Fase 3 cierre — piso_ceramico, categorias completas, tests y golden cases
```

---

## Notas de dominio

- **Piso cerámico vs revestimiento_banio**: piso_ceramico es solo para pisos en ambientes secos (living, cocina, local). Para baño completo (piso + paredes) usar `revestimiento_banio`.
- **Zócalo**: solo generar partidas si `incluye_zocalo=True` Y `perimetro_m > 0`. Si falta alguno de los dos, no generar nada.
- **CSV corruption (bug recurrente)**: siempre verificar el CSV con pandas después de agregar líneas. Nunca usar `echo >>` sin verificar salto de línea.
- **Golden cases**: NUNCA obtener el valor esperado corriendo el código. Calcular con Python puro sin importar `src` o a mano con los precios del CSV.
- **materiales_faltantes()**: firma correcta es `materiales_faltantes(datos, [lista_de_codigos])`. Ver uso correcto en `techo_chapa.py`.
