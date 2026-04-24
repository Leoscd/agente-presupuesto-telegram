# ESTADO DE TAREA - Fase 3

## ✅ COMPLETADO (Fase 2)

- Two-stage routing MiniMax (categorias.py, prompts.py, minimax_client.py, router.py)
- Rubros: mamposteria, losa, contrapiso, revoque_grueso, cubierta_tejas, revestimiento_banio
- Tests: 102 passing — tests/rubros/test_*.py + 18 golden cases
- Datos: CSVs y JSONs actualizados en plantilla y estudio_ramos
- Agentes de revisión: .claude/agents/ (formula-auditor, rubro-reviewer, csv-validator, rubro-fixer, test-writer, pipeline-runner)

## ⚠️ PENDIENTE — Fase 3

- Tarea 1: Rubro `revoque_fino`
- Tarea 2: Rubro `piso_ceramico` (standalone, sin paredes)
- Tarea 3: Actualizar categorias.py + prompts con nuevos rubros
- Tarea 4: Verificación final (pytest 100% + golden cases)

---

# Tareas para el agente de código — Fase 3

> **Leer primero:** El patrón de implementación está en `src/rubros/techo_chapa.py`.
> Seguir ese patrón exacto. No modificar la arquitectura ni los rubros existentes.
>
> **Antes de empezar:** correr `python3 -m pytest tests/ -q` — deben pasar 102 tests.
> Si alguno falla, detener y reportar antes de continuar.

---

## TAREA 1 — Rubro: Revoque fino

### Archivo: `src/rubros/revoque_fino.py`

**Clase `ParamsRevoqueFino(BaseModel)`:**
```python
superficie_m2: PositiveFloat
espesor_cm: float = Field(0.5, ge=0.3, le=1.5)
```

**Constantes:**
```python
# Mortero 1:3 yeso:arena fina
# 1 bolsa yeso (0.020 m3) por cada 0.060 m3 mortero
YESO_M3_POR_BOLSA = Decimal("0.020")
# Plastificante: 1 bidón cada 40 m2
PLASTIFICANTE_POR_M2 = Decimal("0.025")
```

**Agregar al CSV (ambas empresas + plantilla):**
```
YESO_FINO,Yeso fino bolsa 20kg,bolsa,1850.00,2026-04-24
```
Agregar `"YESO_FINO"` a `materiales_disponibles.json`.

Agregar a `precios_mano_obra.csv`:
```
REVOQUE_FINO,Colocación revoque fino enlucido,m2,5200.00,2026-04-24
```

**Fórmulas en `calcular()`:**
```python
sup = Decimal(str(params.superficie_m2))
m3_mortero = _q(sup * Decimal(str(params.espesor_cm)) / Decimal("100"))

# Yeso: ceil(m3 / YESO_M3_POR_BOLSA)
cant_yeso = Decimal(ceil(m3_mortero / YESO_M3_POR_BOLSA))

# Arena fina: m3_mortero * 3
cant_arena = _q(m3_mortero * Decimal("3"))

# Plastificante: max(1, ceil(sup * PLASTIFICANTE_POR_M2))
cant_plastificante = Decimal(max(1, ceil(sup * PLASTIFICANTE_POR_M2)))

# MO: precio_mano_obra(datos, "REVOQUE_FINO") * sup
```

**Partidas (en este orden):**
1. Yeso fino (bolsa, material)
2. Arena fina (m3, material) — usar código `ARENA_FINA` si existe, si no `ARENA_GRUESA`
3. Plastificante Hercal (u, material)
4. Mano de obra revoque fino (m2, mano_obra)

`accion = "revoque_fino"`. Llamar `registrar(...)` al final.

**`metadata`:** `superficie_m2`, `volumen_mortero_m3`, `espesor_cm`

**Tests: `tests/rubros/test_revoque_fino.py`**
- `test_caso_base`: superficie_m2=20, espesor_cm=0.5
- `test_plastificante_minimo`: superficie_m2=10 → cant_plastificante=1
- `test_invariante_suma_igual_total`
- `test_idempotencia` (hypothesis)
- 2 golden cases: 20m2 esp0.5, 50m2 esp1.0

---

## TAREA 2 — Rubro: Piso cerámico / porcelanato

Este rubro cubre **solo piso** (sin paredes). Es distinto a `revestimiento_banio` que maneja piso + paredes. Aplica a living, cocina, locales comerciales.

### Archivo: `src/rubros/piso_ceramico.py`

**Clase `ParamsPisoCeramico(BaseModel)`:**
```python
superficie_m2: PositiveFloat
material: Literal[
    "ceramico_30x30", "ceramico_45x45",
    "porcelanato_60x60", "porcelanato_60x60_premium"
] = "ceramico_45x45"
incluye_zocalo: bool = False
perimetro_m: float = Field(0.0, ge=0.0)  # metros lineales de zócalo
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
ADHESIVO_M2_POR_BOLSA = Decimal("4")        # cerámico
ADHESIVO_PORC_M2_POR_BOLSA = Decimal("3")   # porcelanato
JUNTA_M2_POR_KG = Decimal("3")
ZOCALO_ML_POR_M2 = Decimal("0.10")          # bolsas adhesivo por ml de zócalo
```

**Agregar al CSV (ambas empresas + plantilla) si no existen:**
```
CERAMICO_30X30,Cerámico piso 30x30,m2,8500.00,2026-04-24
CERAMICO_45X45,Cerámico piso 45x45,m2,12800.00,2026-04-24
ZOCALO_CERAMICO,Zócalo cerámico 8x33cm,ml,3200.00,2026-04-24
```
Agregar a `materiales_disponibles.json` los que falten.

Verificar que `PISO_CERAMICO` existe en `precios_mano_obra.csv` (ya fue agregado en Fase 2).

**Fórmulas en `calcular()`:**
```python
sup = Decimal(str(params.superficie_m2))
es_porc = "porcelanato" in params.material
m2_por_bolsa = ADHESIVO_PORC_M2_POR_BOLSA if es_porc else ADHESIVO_M2_POR_BOLSA

# Material con 10% desperdicio
cant_mat = _q(sup * rendimiento(datos, CODIGO_MATERIAL[params.material], Decimal("1.10")))

# Adhesivo
cant_adhesivo = Decimal(ceil(sup / m2_por_bolsa))

# Pastina
cant_junta = Decimal(ceil(sup / JUNTA_M2_POR_KG))

# MO piso
p_mo = precio_mano_obra(datos, "PISO_CERAMICO")
costo_mo = _q(p_mo * sup)

# Zócalo (opcional)
if params.incluye_zocalo and params.perimetro_m > 0:
    perim = Decimal(str(params.perimetro_m))
    cant_zocalo = _q(perim * rendimiento(datos, "ZOCALO_CERAMICO", Decimal("1.05")))
    # MO zócalo: misma tarifa que piso por ml
    costo_mo_zoc = _q(p_mo * perim * Decimal("0.3"))  # 30% del precio piso por ml
```

**Partidas (en este orden):**
1. Material de piso (m2, material)
2. Adhesivo (u/bolsa, material)
3. Pastina/junta (kg, material)
4. Zócalo cerámico (ml, material) — solo si `incluye_zocalo`
5. Mano de obra colocación piso (m2, mano_obra)
6. Mano de obra zócalo (ml, mano_obra) — solo si `incluye_zocalo`

`accion = "piso_ceramico"`. Registrar.

**`metadata`:** `superficie_m2`, `material`, `incluye_zocalo`, `perimetro_m`

**Tests: `tests/rubros/test_piso_ceramico.py`**
- `test_piso_ceramico_sin_zocalo`: superficie_m2=20, material="ceramico_45x45"
- `test_piso_con_zocalo`: superficie_m2=20, incluye_zocalo=True, perimetro_m=18
- `test_porcelanato_usa_adhesivo_flexible`: material="porcelanato_60x60" → adhesivo es ADHESIVO_PORCELANATO
- `test_sin_zocalo_no_genera_partida_zocalo`: incluye_zocalo=False → no hay partida con "zócalo"
- `test_invariante_suma_igual_total`
- `test_idempotencia` (hypothesis)
- 3 golden cases: ceramico 20m2, porcelanato 15m2, ceramico 30m2 con zócalo

---

## TAREA 3 — Actualizar registry y prompts

### `src/rubros/categorias.py`

Actualizar `terminaciones` con los nuevos rubros:
```python
"terminaciones": ["revoque_grueso", "revoque_fino", "piso_ceramico", "revestimiento_banio"],
```

### `src/rubros/__init__.py`

Agregar imports:
```python
from src.rubros import revoque_fino, piso_ceramico  # noqa: F401
```

### `src/orquestador/prompts.py` — `SYSTEM_PROMPT`

Agregar en la sección "Acciones disponibles":

```
9. "revoque_fino":
   - superficie_m2: float
   - espesor_cm: float (default 0.5)

10. "piso_ceramico":
    - superficie_m2: float
    - material: "ceramico_30x30" | "ceramico_45x45" | "porcelanato_60x60" | "porcelanato_60x60_premium"
    - incluye_zocalo: bool (default false)
    - perimetro_m: float (metros lineales de zócalo, default 0)
```

---

## TAREA 4 — Verificación final

```bash
# Todos los tests deben pasar
python3 -m pytest tests/ -q
# Resultado esperado: >= 120 passed

# Registry debe incluir los nuevos rubros
python3 -c "from src.rubros import REGISTRY; print(list(REGISTRY.keys()))"
# Debe incluir: [..., 'revoque_fino', 'piso_ceramico']

# Smoke test por rubro nuevo
python3 -c "
import src.rubros
from src.rubros.base import REGISTRY
r = REGISTRY['revoque_fino'].calcular(
    __import__('src.rubros.revoque_fino', fromlist=['ParamsRevoqueFino']).ParamsRevoqueFino(superficie_m2=20),
    'estudio_ramos'
)
print('revoque_fino total:', r.total)
r2 = REGISTRY['piso_ceramico'].calcular(
    __import__('src.rubros.piso_ceramico', fromlist=['ParamsPisoCeramico']).ParamsPisoCeramico(superficie_m2=20),
    'estudio_ramos'
)
print('piso_ceramico total:', r2.total)
"
```

Hacer commit:
```
feat: Fase 3 — revoque_fino, piso_ceramico, categorias actualizadas
```

---

## Notas de dominio — Fase 3

- **Revoque fino**: se aplica sobre revoque grueso ya seco. Usa yeso fino + arena fina + plastificante. Espesor típico 5mm.
- **Arena fina vs gruesa**: el revoque fino usa arena fina (más tamizada). Si no existe `ARENA_FINA` en el CSV de la empresa, usar `ARENA_GRUESA` como fallback con advertencia.
- **Piso cerámico standalone**: cubre solo pisos (living, cocina, baño solo piso). Para baño completo (piso + paredes) usar `revestimiento_banio`.
- **Zócalo**: es opcional. Solo genera partidas si `incluye_zocalo=True` y `perimetro_m > 0`.
- **Desperdicio estándar**: 10% para todos los materiales de piso.
