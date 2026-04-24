# Tareas para el agente de código
> **Fecha:** 2026-04-24  
> **Estado del proyecto:** Pipeline E2E funcionando (techo ✅ mampostería ✅ baño ✅), pytest 6/6 ✅, golden 3/3 ✅

---

## CONTEXTO TÉCNICO CLAVE

### Cómo funciona el proyecto
- **MiniMax-M2** solo extrae intención (JSON). **Python** calcula todo. Nunca pedirle al modelo que calcule precios.
- Pipeline: clasificar_categoria() → parsear() → despachar() → ResultadoPresupuesto
- Decimal para todo lo que sea dinero. Nunca float en cálculos de precio.
- Registry pattern: cada rubro = 1 archivo en `src/rubros/`. Registrar con `registrar(CalcXxx())` al final del archivo.
- CSV de precios en `empresas/{id}/precios_materiales.csv` y `precios_mano_obra.csv`. Editar el CSV cambia precios — no hay que tocar código.

### Bugs conocidos que YA están corregidos (no volver a introducirlos)
- MiniMax envuelve el JSON en ` ```json ``` ` → `_strip_think()` los stripea con `_FENCE_RE`
- `math.sqrt()` no acepta Decimal → convertir a float primero, luego `Decimal(str(...))`
- Multiplicar float × Decimal da TypeError → hacer `Decimal(str(float_val))` antes
- Cal hidráulica no se usa → usar `PLASTIFICANTE_HERCAL` (bidon 20L)

### Archivos críticos
```
src/rubros/base.py          — interfaz Calculadora, Partida, ResultadoPresupuesto, REGISTRY
src/rubros/__init__.py      — importa todos los rubros (trigger auto-registro)
src/datos/loader.py         — cargar_empresa(), precio_material(), precio_mano_obra()
src/orquestador/prompts.py  — SYSTEM_PROMPT (lista TODAS las acciones disponibles)
src/orquestador/minimax_client.py — parsear(), clasificar_categoria()
empresas/_plantilla/        — CSV plantilla con todos los materiales
```

---

## TAREA 1 — Tests unitarios para todos los rubros nuevos
**Prioridad: ALTA**

Crear un archivo de tests por cada rubro que no tiene tests todavía. Modelo a seguir: `tests/rubros/test_techo_chapa.py`.

### Archivos a crear:

#### `tests/rubros/test_mamposteria.py`
Casos obligatorios:
- `test_muro_hueco_12_5x3()` → largo=5, alto=3, tipo="hueco_12"
  - Verificar ladrillos: `ceil(15m2 * 60 ladrillos/m2 * 1.05) = 945 u`
  - Verificar total > 0 y suma de partidas == total
- `test_muro_comun_sin_plastificante()` — tipo="comun", verificar que hay partida de ladrillo común
- `test_invariante_suma_partidas_igual_total()` — property test con hypothesis
- `test_alto_cero_falla()` — alto=0 debe lanzar ValidationError

#### `tests/rubros/test_losa.py`
Casos obligatorios:
- `test_losa_4x5_12cm()` → ancho=4, largo=5, espesor_cm=12
  - m3 = 4*5*0.12 = 2.4 m3
  - cemento = ceil(2.4 * 7) = 17 bolsas
  - Verificar suma partidas == total
- `test_espesor_default_es_12cm()` — sin pasar espesor_cm, debe calcular con 12
- `test_invariante_hypothesis()` — monotonía: mayor superficie → mayor total

#### `tests/rubros/test_contrapiso.py`
- `test_contrapiso_20m2_8cm()` → superficie=20, espesor=8 → m3 = 1.6
  - cemento = ceil(1.6 * 4) = 7 bolsas
- `test_invariante_suma_partidas()`
- `test_espesor_minimo()` — espesor_cm muy pequeño no debe crashear

#### `tests/rubros/test_revoque_grueso.py`
- `test_revoque_30m2()` → superficie=30, espesor=1.5
  - m3 = 30 * 0.015 = 0.45
  - plastificante: ceil(30/30) = 1 bidón
- `test_invariante_suma_partidas()`

#### `tests/rubros/test_cubierta_tejas.py`
- `test_teja_ceramica_5x8_30pct()` → ancho=5, largo=8, pendiente=30
  - factor = sqrt(1 + 0.3²) ≈ 1.0440
  - m2_real ≈ 41.76
  - tejas = ceil(41.76 * 16 * 1.10) = 735 u
- `test_teja_cemento_vs_ceramica()` — misma superficie, teja cemento debe ser más barata
- `test_invariante_suma_partidas()`

#### `tests/rubros/test_revestimiento_banio.py`
- `test_banio_completo_6m2_piso_18m2_pared()` → confirmar total = $698,700 ARS
- `test_solo_piso()` → superficie_pared_m2=0
- `test_solo_pared()` → superficie_piso_m2=0
- `test_con_alzada_cocina()` → incluye_alzada_cocina=True, superficie_alzada_m2=4
- `test_sin_superficie_falla()` → piso=0 y pared=0 debe lanzar ValidationError

**Instrucción importante:** todos los tests deben pasar con `pytest tests/ -v`. No usar mocks para precios — usar `empresa_id="estudio_ramos"` con datos reales.

---

## TAREA 2 — Casos golden para rubros nuevos
**Prioridad: ALTA**

Agregar casos al archivo `tests/golden/casos.yaml`. Actualmente solo tiene 3 casos de techo_chapa.

### Formato de cada caso (seguir exactamente):
```yaml
- id: mamposteria_001
  descripcion: "muro hueco 12 de 5x3 — caso testigo"
  empresa: estudio_ramos
  accion: mamposteria
  parametros:
    largo: 5
    alto: 3
    tipo: hueco_12
  esperado:
    total: 482940.00        # <-- calcular con Python primero, luego poner el valor exacto
    tolerancia_pct: 0.1     # 0.1% = prácticamente exacto (mismo código, mismos precios)
    partidas_minimas: 5
```

### Casos a agregar:
1. `mamposteria_001` — hueco_12 5x3 → total exacto a calcular
2. `mamposteria_002` — hueco_18 4x2.8 → total exacto a calcular  
3. `losa_001` — 4x5 espesor 12cm → total exacto a calcular
4. `contrapiso_001` — 20m2 espesor 8cm → total exacto a calcular
5. `revoque_001` — 30m2 espesor 1.5cm → total exacto a calcular
6. `cubierta_tejas_001` — ceramica 5x8 30% → total exacto a calcular
7. `revestimiento_001` — baño porcelanato 6m2 piso + 18m2 pared ceramico → total = 698700.00

**Para calcular los totales exactos**, correr:
```bash
python -c "
import src.rubros
from src.orquestador.router import despachar
from decimal import Decimal

casos = [
    ('mamposteria', {'largo': 5, 'alto': 3, 'tipo': 'hueco_12'}),
    ('mamposteria', {'largo': 4, 'alto': 2.8, 'tipo': 'hueco_18'}),
    ('losa', {'ancho': 4, 'largo': 5, 'espesor_cm': 12}),
    ('contrapiso', {'superficie_m2': 20, 'espesor_cm': 8}),
    ('revoque_grueso', {'superficie_m2': 30, 'espesor_cm': 1.5}),
    ('cubierta_tejas', {'ancho': 5, 'largo': 8, 'pendiente_pct': 30, 'tipo_teja': 'ceramica_colonial'}),
]
for accion, params in casos:
    r = despachar(accion, params, 'estudio_ramos')
    print(f'{accion}: {r.total}')
"
```

---

## TAREA 3 — Rubro: instalacion_electrica
**Prioridad: MEDIA**

Crear `src/rubros/instalacion_electrica.py` siguiendo el patrón de los otros rubros.

### Parámetros del modelo:
```python
class ParamsInstalacionElectrica(BaseModel):
    superficie_m2: PositiveFloat          # superficie del local/vivienda
    tipo: Literal["basica", "completa"]   # basica = 1 circuito, completa = 2+ circuitos
    cantidad_bocas: int = Field(0, ge=0)  # si 0, calcular por m2
    incluye_tablero: bool = True
```

### Fórmulas aproximadas (ajustar según criterio):
- Bocas: si `cantidad_bocas == 0` → `ceil(superficie_m2 / 4)` bocas (aprox 1 cada 4m2)
- Cable: bocas * 3.5 ml por boca (promedio recorrido)
- Caño corrugado: cable_ml * 1.1
- Tablero monofásico: 1 u (si incluye_tablero)
- Llaves/tomacorrientes: bocas unidades
- MO: tarifa "INSTALACION_ELECTRICA" * superficie_m2

### Materiales a agregar en CSV (ambas empresas + _plantilla):
Agregar al final de `precios_materiales.csv`:
```
CABLE_IRAM_2X2_5,Cable IRAM 2x2.5mm bipolar,ml,850.00,2026-04-24
CABLE_IRAM_2X4,Cable IRAM 2x4mm bipolar,ml,1250.00,2026-04-24
CANO_CORRUGADO_20,Caño corrugado plástico 20mm,ml,320.00,2026-04-24
TABLERO_MONOF_12,Tablero monofásico 12 módulos,u,38000.00,2026-04-24
LLAVE_SIMPLE,Llave simple Cambre/similar,u,4500.00,2026-04-24
TOMACORRIENTE_2P,Tomacorriente 2P+T Cambre/similar,u,5800.00,2026-04-24
```

Agregar en `precios_mano_obra.csv`:
```
INSTALACION_ELECTRICA,Instalación eléctrica completa,m2,8500.00,
```

### Agregar en `src/orquestador/prompts.py` — SYSTEM_PROMPT:
```
9. "instalacion_electrica": superficie_m2, tipo("basica"|"completa"), cantidad_bocas(default 0), incluye_tablero(bool, default true)
```
Y un ejemplo en los EJEMPLOS.

### Registrar en `src/rubros/__init__.py`:
```python
from src.rubros.instalacion_electrica import CalcInstalacionElectrica  # noqa: F401
```

### Tests en `tests/rubros/test_instalacion_electrica.py`:
- `test_basica_50m2()` → superficie=50, tipo="basica"
- `test_completa_con_bocas_definidas()` → superficie=80, tipo="completa", cantidad_bocas=20
- `test_invariante_suma_partidas()`

---

## TAREA 4 — Rubro: instalacion_sanitaria
**Prioridad: MEDIA**

Crear `src/rubros/instalacion_sanitaria.py`.

### Parámetros del modelo:
```python
class ParamsInstalacionSanitaria(BaseModel):
    cantidad_banos: int = Field(1, ge=1, le=10)
    cantidad_cocinas: int = Field(0, ge=0, le=5)
    metros_lineales_agua_fria: float = Field(0.0, ge=0)   # si 0, calcular por cant
    metros_lineales_desague: float = Field(0.0, ge=0)
    tipo_cano: Literal["pvc", "polipropileno"] = "pvc"
```

### Fórmulas:
- Si ml_agua_fria == 0: `cantidad_banos * 8 + cantidad_cocinas * 5` ml (estimado)
- Si ml_desague == 0: `(cantidad_banos + cantidad_cocinas) * 10` ml
- Codos y uniones: `ml_total * 0.3` (30% en accesorios)

### Materiales a agregar en CSVs:
```
CANO_PVC_32,Caño PVC presión 32mm barra 6m,u,8500.00,2026-04-24
CANO_PVC_50,Caño PVC desague 50mm barra 4m,u,6800.00,2026-04-24
CANO_PVC_110,Caño PVC desague 110mm barra 4m,u,12500.00,2026-04-24
CODO_PVC_32,Codo PVC 32mm 90°,u,850.00,2026-04-24
UNION_PVC_32,Union PVC 32mm,u,620.00,2026-04-24
SELLADOR_TEFLON,Cinta teflon rollo,u,350.00,2026-04-24
```

Agregar en MO:
```
INSTALACION_SANITARIA,Instalación sanitaria completa,u,85000.00,
```
(precio por baño/cocina, no por m2)

---

## TAREA 5 — Agregar CERAMICO_30X30 y CERAMICO_45X45 en CSVs
**Prioridad: MEDIA**

El SYSTEM_PROMPT menciona `"ceramico_30x30"` y `"ceramico_45x45"` como opciones de `material_piso` pero no están en los CSVs. Agregar en ambas empresas y `_plantilla`:

```
CERAMICO_30X30,Cerámico piso 30x30 esmaltado,m2,9800.00,2026-04-24
CERAMICO_45X45,Cerámico piso 45x45 esmaltado,m2,12500.00,2026-04-24
```

Y en `src/rubros/revestimiento_banio.py` actualizar el dict `CODIGO_MATERIAL`:
```python
CODIGO_MATERIAL = {
    "porcelanato_60x60": "PORCELANATO_60X60",
    "porcelanato_60x60_premium": "PORCELANATO_60X60_PREMIUM",
    "ceramico_pared_25x35": "CERAMICO_PARED_25X35",
    "ceramico_30x30": "CERAMICO_30X30",    # agregar
    "ceramico_45x45": "CERAMICO_45X45",    # agregar
}
```

Y el `ParamsRevestimientoBanio` actualizar los Literal types:
```python
material_piso: Literal[
    "porcelanato_60x60", "porcelanato_60x60_premium",
    "ceramico_30x30", "ceramico_45x45"
]
material_pared: Literal[
    "porcelanato_60x60", "ceramico_pared_25x35", "ceramico_30x30"
]
```

---

## TAREA 6 — Rubro: revoque_fino
**Prioridad: BAJA**

Crear `src/rubros/revoque_fino.py` (terminación antes de pintar).

### Parámetros:
```python
class ParamsRevoqueFino(BaseModel):
    superficie_m2: PositiveFloat
    espesor_cm: float = Field(0.5, ge=0.3, le=1.0)
```

### Fórmulas:
- m3 = superficie_m2 * espesor_cm / 100
- Yeso o cal fina: aprox 15 kg/m2 de superficie (no en volumen, sino por superficie)
- Usar material `YESO_BOLSA` (agregar al CSV si no existe: `YESO_BOLSA,Yeso bolsa 40kg,u,8500.00,2026-04-24`)
- Rendimiento yeso: 1 bolsa de 40kg cubre aprox 8m2 → `ceil(superficie_m2 / 8)` bolsas
- MO: tarifa "REVOQUE_FINO" (agregar al CSV MO: `REVOQUE_FINO,Revoque fino yeso,m2,2800.00,`)

---

## TAREA 7 — Mejorar el template PDF default
**Prioridad: BAJA**

Ubicación: `src/pdf/templates/default/presupuesto.html.j2` y `styles.css`

El template actual es funcional pero básico. Mejorar con:

1. **Header**: logo del estudio (variable `{{ empresa.logo_url }}` si existe, sino placeholder elegante con iniciales)
2. **Tabla de partidas**: zebra stripes, alineación derecha en columnas numéricas, separador visual entre secciones material/mano_obra
3. **Subtotales con formato visual**: destacar TOTAL con fondo oscuro y texto blanco
4. **Footer**: datos del estudio (CUIT, teléfono, email desde `config.json`) + "Válido por 30 días"
5. **Watermark de borrador**: si `metadata.borrador == True`, texto diagonal "BORRADOR"

Variables disponibles en el template (ya definidas en `pdf/generador.py`):
```
{{ empresa.nombre }}
{{ empresa.cuit }}
{{ empresa.telefono }}
{{ empresa.email }}
{{ presupuesto.rubro }}
{{ presupuesto.partidas }}  — lista de Partida
{{ presupuesto.total }}
{{ presupuesto.subtotal_materiales }}
{{ presupuesto.subtotal_mano_obra }}
{{ presupuesto.advertencias }}
{{ fecha_generacion }}  — string "24 de abril de 2026"
```

---

## TAREA 8 — Comando /admin tokens en el bot
**Prioridad: BAJA**

En `src/bot/handlers.py` agregar un comando `/admin` que:
1. Solo responda a un `ADMIN_CHAT_ID` (agregar a `.env` y `src/config.py`)
2. Muestre el consumo acumulado de tokens MiniMax:
   ```
   📊 Consumo MiniMax
   Input: 145,230 tokens ($0.044)
   Output: 23,410 tokens ($0.028)
   Total: $0.072 USD de $10.00 presupuestados (0.72%)
   Presupuestos generados: 47
   Último reset: 2026-04-01
   ```
3. Leer los datos desde `src/persistencia/db.py` — función `get_resumen_tokens()` (crearla si no existe)

La tabla `tokens_log` en SQLite ya existe con campos: `fecha`, `tokens_input`, `tokens_output`, `usd`.

---

## TAREA 9 — Script de validación cruzada multi-empresa
**Prioridad: BAJA**

Crear `scripts/validar_multi_empresa.py`.

El script debe:
1. Calcular el mismo presupuesto técnico en `estudio_ramos` y en `_plantilla` (que tienen los mismos precios base)
2. Verificar que los totales sean iguales (mismos precios → mismo total)
3. Después crear `empresa_test_precios_dobles` en memoria con precios×2 y verificar total×2

Casos a validar:
- techo_chapa galvanizada 7x10 C100
- mamposteria hueco_12 5x3
- losa 4x5 12cm

Output esperado:
```
[OK] techo_chapa: estudio_ramos=$1,374,380 == _plantilla=$1,374,380
[OK] mamposteria: estudio_ramos=$482,940 == _plantilla=$482,940
[FAIL] losa: estudio_ramos=$X != _plantilla=$Y  ← detectaría inconsistencia
```

---

## VERIFICACIÓN FINAL (correr antes de hacer PR)

```bash
# Desde D:\agente-presupuesto-telegram\

# 1. Tests unitarios
.venv/Scripts/python -m pytest tests/ -v

# 2. Golden dataset
PYTHONPATH=. .venv/Scripts/python scripts/correr_golden.py

# 3. Pipeline E2E (requiere conexión a internet — MiniMax API)
.venv/Scripts/python -c "
import asyncio, src.rubros
from src.persistencia.db import init_db; init_db()
from src.orquestador.minimax_client import parsear
from src.orquestador.router import despachar
from src.datos.loader import cargar_empresa

async def t():
    for txt in ['techo chapa 7x10 galvanizada C100', 'muro hueco 12 de 5x3', 'losa 4x5', 'contrapiso 20m2', 'revoque grueso 30m2']:
        datos = cargar_empresa('estudio_ramos')
        r = await parsear(txt, datos.materiales_disponibles[:8])
        if r.accion != 'aclaracion':
            res = despachar(r.accion, r.parametros, 'estudio_ramos')
            print(f'OK {r.accion}: {res.total}')
        else:
            print(f'ACLARACION: {r.parametros}')

asyncio.run(t())
"
```

---

## NOTAS IMPORTANTES PARA EL AGENTE

1. **No tocar `.env`** — contiene la API key de MiniMax real.
2. **No tocar `empresas/estudio_ramos/`** sin agregar el mismo cambio en `empresas/_plantilla/`.
3. **Decimal para dinero siempre** — si ves `float` en cálculos de precio, es un bug.
4. **`_q()` está definido en cada rubro** como `v.quantize(Decimal("0.01"), ROUND_HALF_UP)` — usarlo en subtotales.
5. **Registrar siempre** — al final de cada rubro nuevo, `registrar(CalcXxx())`.
6. **Importar en `__init__.py`** — agregar `from src.rubros.nuevo_rubro import CalcNuevoRubro  # noqa: F401`.
7. **SYSTEM_PROMPT debe ser exhaustivo** — cada acción nueva debe quedar documentada en `src/orquestador/prompts.py` con su ejemplo.
8. **Los tests deben ser determinísticos** — no mockear precios, usar `estudio_ramos` real para que fallen si cambia algo importante.
