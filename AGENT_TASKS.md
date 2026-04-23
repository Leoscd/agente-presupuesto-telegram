# Tareas para el agente de código — Fase 2

> **Leer primero:** El patrón de implementación de rubros está en `src/rubros/techo_chapa.py`.
> Seguir ese patrón exacto para cada rubro nuevo. El agente NO debe modificar la arquitectura.

---

## CORRECCIONES AL CSV ANTES DE EMPEZAR

### 1. Reemplazar cal hidráulica por plastificante Hercal/Plasticor

La cal hidráulica **no se usa** en obra argentina actual. El plastificante de mortero es **Hercal** o **Plasticor** (marcas comerciales del mismo producto).

**En `empresas/_plantilla/precios_materiales.csv` y `empresas/estudio_ramos/precios_materiales.csv`:**

Eliminar la línea:
```
CAL_HIDRAULICA,Cal hidráulica bolsa 25kg,u,4200.00,2026-04-23
```

Reemplazar por:
```
PLASTIFICANTE_HERCAL,Plastificante Hercal/Plasticor bidon 20L,u,18500.00,2026-04-23
```

**En `materiales_disponibles.json`** (ambas empresas + plantilla): reemplazar `"CAL_HIDRAULICA"` por `"PLASTIFICANTE_HERCAL"`.

**Dosis de uso:** 1 bidón cada 25 m2 de mampostería (o cada 20 m2 de piso cerámico). Usar esta constante en las calculadoras.

---

## TAREA 1 — Two-stage routing (arquitectura de grupos)

### 1a. Crear `src/rubros/categorias.py`

```python
CATEGORIAS: dict[str, list[str]] = {
    "cubiertas":     ["techo_chapa", "cubierta_tejas"],
    "obra_gruesa":   ["mamposteria", "losa", "contrapiso"],
    "terminaciones": ["revoque_grueso", "revoque_fino", "piso_ceramico", "revestimiento_banio"],
    "instalaciones": [],  # fase 3
}
```

### 1b. Modificar `src/orquestador/prompts.py`

Agregar constante `SYSTEM_PROMPT_CATEGORIA`:

```python
SYSTEM_PROMPT_CATEGORIA = """Clasificá el pedido en UNA de estas categorías:
- cubiertas: techos de chapa, tejas, membrana, losa de cubierta
- obra_gruesa: mampostería, losa entre pisos, contrapiso, encadenados
- terminaciones: revoques, pisos, cerámicos, porcelanato, revestimientos
- instalaciones: electricidad, sanitaria, gas

Devolvé SOLO JSON: {"categoria": "<nombre>", "confianza": <0.0-1.0>}"""
```

Modificar `build_user_message()` para aceptar `acciones_filtradas: list[str] | None = None`.
Si se pasa, agregar al mensaje: `"Acciones disponibles en este contexto: {acciones_filtradas}"`.

### 1c. Modificar `src/orquestador/minimax_client.py`

Agregar función:
```python
async def clasificar_categoria(texto: str) -> tuple[str, float]:
    # Llamar MiniMax con SYSTEM_PROMPT_CATEGORIA + texto
    # Retornar (categoria, confianza) del JSON de respuesta
    # Si falla o confianza < 0.6 → retornar ("", 0.0)
```

Modificar `parsear()` para aceptar `acciones_filtradas: list[str] | None = None`.
Pasarlo a `build_user_message()`.

### 1d. Agregar `despachar_con_pipeline()` en `src/orquestador/router.py`

```python
async def despachar_con_pipeline(
    texto: str, empresa_id: str, materiales_disponibles: list[str]
) -> tuple[ResultadoPresupuesto, RespuestaOrq]:
    """Two-stage: clasificar categoría → parsear acción filtrada → calcular."""
    from src.rubros.categorias import CATEGORIAS
    from src.orquestador.minimax_client import clasificar_categoria, parsear

    cat, conf_cat = await clasificar_categoria(texto)
    if cat and conf_cat >= 0.8:
        acciones = CATEGORIAS.get(cat, [])
    else:
        acciones = None  # sin filtro

    resp = await parsear(texto, materiales_disponibles, acciones_filtradas=acciones)
    if resp.accion == "aclaracion":
        # No calcular, retornar para que el handler pregunte
        return None, resp  # type: ignore[return-value]
    resultado = despachar(resp.accion, resp.parametros, empresa_id)
    return resultado, resp
```

Actualizar `src/bot/handlers.py` → función `on_mensaje()` para llamar `despachar_con_pipeline()` en vez de `minimax_client.parsear()` + `router.despachar()` por separado.

---

## TAREA 2 — Rubro: Mampostería

### Archivo: `src/rubros/mamposteria.py`

**Clase `ParamsMamposteria(BaseModel)`:**
```python
largo: PositiveFloat        # metros lineales de muro
alto: PositiveFloat         # altura en metros
tipo: Literal["hueco_12", "hueco_18", "comun"] = "hueco_12"
```

**Constantes internas:**
```python
CODIGO_LADRILLO = {
    "hueco_12": "LADRILLO_HUECO_12",
    "hueco_18": "LADRILLO_HUECO_18",
    "comun":    "LADRILLO_COMUN",
}
CODIGO_TAREA_MO = {
    "hueco_12": "MAMPOSTERIA_HUECO_12",
    "hueco_18": "MAMPOSTERIA_HUECO_18",
    "comun":    "MAMPOSTERIA_COMUN",
}
LADRILLOS_POR_M2 = {
    "hueco_12": Decimal("36"),
    "hueco_18": Decimal("28"),
    "comun":    Decimal("48"),
}
PLASTIFICANTE_POR_M2 = Decimal("0.04")  # bidones por m2 (1 bidón cada 25m2)
```

**Fórmulas en `calcular()`:**
```python
m2 = largo * alto

# Ladrillos
cant_ladrillos = ceil(m2 * LADRILLOS_POR_M2[tipo] * rendimiento(datos, cod_ladrillo, Decimal("1.05")))

# Mortero seco (cemento en bolsas): 1 bolsa cada 10 m2
cant_cemento = ceil(m2 / Decimal("10"))

# Plastificante Hercal/Plasticor: 1 bidón cada 25 m2
cant_plastificante = ceil(m2 * PLASTIFICANTE_POR_M2)

# Arena gruesa: 0.03 m3 por m2
cant_arena = _q(m2 * Decimal("0.03"))

# Mano de obra: precio_mano_obra(datos, CODIGO_TAREA_MO[tipo]) * m2
```

**Partidas (en este orden):**
1. Ladrillo (concepto dinámico según tipo, unidad "u", categoria "material")
2. Cemento portland (bolsa, "material")
3. Plastificante Hercal/Plasticor (u, "material")
4. Arena gruesa (m3, "material")
5. Mano de obra mampostería (m2, "mano_obra")

`accion = "mamposteria"`. Llamar `registrar(...)` al final del archivo.

### Test: `tests/rubros/test_mamposteria.py`

```python
EMPRESA = "estudio_ramos"

def test_muro_hueco12_5x3():
    r = _calc(largo=5, alto=3, tipo="hueco_12")
    assert r.metadata["superficie_m2"] == 15.0
    # ladrillos: ceil(15 * 36 * 1.05) = ceil(567) = 567
    # cemento: ceil(15/10) = 2
    # plastificante: ceil(15 * 0.04) = 1
    # arena: 15 * 0.03 = 0.45 m3
    ladr = next(p for p in r.partidas if "ladrillo" in p.concepto.lower())
    assert ladr.cantidad == Decimal("567")

def test_invariante_suma_igual_total()  # igual que en techo_chapa
def test_propiedad_monotonia()          # hypothesis: más m2 → más total
def test_propiedad_idempotencia()       # hypothesis: mismo input → mismo resultado
```

**Agregar 3 casos a `tests/golden/casos.yaml`** (calcular manualmente con los precios de `estudio_ramos`):
- `mamposteria_001`: largo=5, alto=3, tipo=hueco_12
- `mamposteria_002`: largo=10, alto=2.8, tipo=hueco_18
- `mamposteria_003`: largo=8, alto=3, tipo=comun

---

## TAREA 3 — Rubro: Losa de hormigón armado

### Archivo: `src/rubros/losa.py`

**Clase `ParamsLosa(BaseModel)`:**
```python
ancho: PositiveFloat
largo: PositiveFloat
espesor_cm: float = Field(12.0, ge=8.0, le=25.0)
```

**Fórmulas (dosificación H21):**
```python
m2 = ancho * largo
m3 = _q(m2 * Decimal(str(espesor_cm)) / Decimal("100"))

# Por m3: 7 bolsas cemento, 0.45 m3 arena, 0.65 m3 piedra
cant_cemento = ceil(m3 * Decimal("7"))
cant_arena   = _q(m3 * Decimal("0.45"))
cant_piedra  = _q(m3 * Decimal("0.65"))

# Hierro 8mm: 1.2 barras por m2 (doble malla, ambas direcciones)
cant_h8 = ceil(m2 * Decimal("1.2"))

# Plastificante: 1 bidón cada 15 m3 de hormigón
cant_plastificante = max(1, ceil(m3 / Decimal("15")))

# Mano de obra: precio_mano_obra(datos, "LOSA_HORMIGON") * m2
```

**Partidas:**
1. Cemento portland (bolsa, material)
2. Arena gruesa (m3, material)
3. Piedra partida 6-12mm (m3, material)
4. Hierro nervado 8mm (u, material)
5. Plastificante Hercal (u, material)
6. Mano de obra losa (m2, mano_obra)

`accion = "losa"`. Registrar.

**Tests:** caso base 4x5 espesor 12cm. Invariante suma, monotonía, idempotencia. 3 casos golden.

---

## TAREA 4 — Rubro: Contrapiso de hormigón

### Archivo: `src/rubros/contrapiso.py`

**Clase `ParamsContrapiso(BaseModel)`:**
```python
superficie_m2: PositiveFloat
espesor_cm: float = Field(8.0, ge=5.0, le=15.0)
```

**Fórmulas (hormigón pobre H13):**
```python
m3 = _q(sup * Decimal(str(espesor_cm)) / Decimal("100"))

# Por m3: 4 bolsas cemento, 0.55 m3 arena, 0.65 m3 piedra
cant_cemento = ceil(m3 * Decimal("4"))
cant_arena   = _q(m3 * Decimal("0.55"))
cant_piedra  = _q(m3 * Decimal("0.65"))

# Mano de obra: precio_mano_obra(datos, "CONTRAPISO") * m2
```

`accion = "contrapiso"`. Tests + 2 casos golden.

---

## TAREA 5 — Rubro: Revoque grueso interior

### Archivo: `src/rubros/revoque_grueso.py`

**Clase `ParamsRevoqueGrueso(BaseModel)`:**
```python
superficie_m2: PositiveFloat
espesor_cm: float = Field(1.5, ge=0.5, le=3.0)
```

**Fórmulas (mortero 1:3 cemento-arena):**
```python
m3_mortero = _q(sup * Decimal(str(espesor_cm)) / Decimal("100"))

# 1 bolsa cemento (0.035 m3) por cada 0.105 m3 mortero (relación 1:3)
cant_cemento = ceil(m3_mortero / Decimal("0.035"))
cant_arena   = _q(m3_mortero * Decimal("3"))

# Plastificante: 1 bidón cada 30 m2
cant_plastificante = max(1, ceil(sup / Decimal("30")))

# Mano de obra: "REVOQUE_GRUESO" * m2
```

`accion = "revoque_grueso"`. Tests + 2 casos golden.

---

## TAREA 6 — Rubro: Cubiertas de tejas

### Archivo: `src/rubros/cubierta_tejas.py`

Agregar al CSV (ambas empresas + plantilla):
```
TEJA_CERAMICA_COL,Teja cerámica colonial,u,850.00,2026-04-23
TEJA_CEMENTO,Teja de cemento,u,620.00,2026-04-23
LISTÓN_MADERA_2X3,Listón de madera 2x3" x 3m,u,4800.00,2026-04-23
CUMBRERA_CERAMICA,Cumbrera cerámica,u,1200.00,2026-04-23
```
Agregar a `materiales_disponibles.json`.

**Clase `ParamsCubiertaTejas(BaseModel)`:**
```python
ancho: PositiveFloat
largo: PositiveFloat
tipo_teja: Literal["ceramica_colonial", "cemento"] = "ceramica_colonial"
pendiente_pct: float = Field(30.0, ge=15.0, le=60.0)  # pendiente en %
```

**Fórmulas:**
```python
# Superficie real con pendiente
factor_pendiente = (1 + (Decimal(str(pendiente_pct)) / Decimal("100")) ** 2).sqrt()
m2_real = _q(ancho * largo * factor_pendiente)

CODIGO_TEJA = {"ceramica_colonial": "TEJA_CERAMICA_COL", "cemento": "TEJA_CEMENTO"}
TEJAS_POR_M2 = {"ceramica_colonial": Decimal("16"), "cemento": Decimal("12")}

# Tejas con 10% desperdicio
cant_tejas = ceil(m2_real * TEJAS_POR_M2[tipo] * Decimal("1.10"))

# Listones: 1 liston cada 3 tejas de ancho, aprox 1 listón por m2
cant_listones = ceil(m2_real * Decimal("1.2"))

# Cumbreras: largo / 0.30m (largo de cada pieza)
cant_cumbreras = ceil(Decimal(str(largo)) / Decimal("0.30"))

# Mano de obra: nueva tarea "CUBIERTA_TEJAS" — agregar al CSV precios_mano_obra
# precio sugerido: 6500 ARS/m2
```

Agregar `CUBIERTA_TEJAS,Colocación cubierta de tejas,m2,6500.00,2` al CSV `precios_mano_obra.csv` (ambas empresas + plantilla).

`accion = "cubierta_tejas"`. Tests + 2 casos golden.

---

## TAREA 7 — Rubro: Revestimiento de baño/cocina

Este rubro es el más flexible: piso y paredes pueden ser materiales distintos. Debe manejar:
- Solo piso
- Solo paredes
- Ambos con el mismo material
- Ambos con materiales distintos (caso cocina con alzada de mesada)

### Agregar al CSV materiales (ambas empresas + plantilla):
```
PORCELANATO_60X60,Porcelanato rectificado 60x60 standard,m2,22500.00,2026-04-23
PORCELANATO_60X60_PREMIUM,Porcelanato rectificado 60x60 premium,m2,38000.00,2026-04-23
CERAMICO_PARED_25X35,Cerámico pared 25x35 esmaltado,m2,14500.00,2026-04-23
ADHESIVO_PORCELANATO,Adhesivo flexible para porcelanato bolsa 25kg,u,12500.00,2026-04-23
JUNTA_PORCELANATO,Pastina/junta porcelanato kg,u,1800.00,2026-04-23
```

Agregar `"PISO_CERAMICO"` y `"REVESTIMIENTO_CERAMICO"` como tareas en `precios_mano_obra.csv` si no existen:
```
REVESTIMIENTO_CERAMICO,Colocación revestimiento cerámico paredes,m2,7800.00,2
```

Agregar todos los nuevos códigos a `materiales_disponibles.json`.

### Archivo: `src/rubros/revestimiento_banio.py`

**Clase `ParamsRevestimientoBanio(BaseModel)`:**
```python
superficie_piso_m2: float = Field(0.0, ge=0.0)
superficie_pared_m2: float = Field(0.0, ge=0.0)
material_piso: Literal[
    "porcelanato_60x60", "porcelanato_60x60_premium", "ceramico_30x30", "ceramico_45x45"
] = "porcelanato_60x60"
material_pared: Literal[
    "porcelanato_60x60", "porcelanato_60x60_premium", "ceramico_pared_25x35", "ceramico_30x30"
] = "ceramico_pared_25x35"
incluye_alzada_cocina: bool = False
superficie_alzada_m2: float = Field(0.0, ge=0.0)  # zócalo alto de mesada

@model_validator(mode="after")
def al_menos_una_superficie(self):
    if self.superficie_piso_m2 == 0 and self.superficie_pared_m2 == 0:
        raise ValueError("Debe especificar superficie de piso y/o paredes")
    return self
```

**Códigos:**
```python
CODIGO_MATERIAL: dict[str, str] = {
    "porcelanato_60x60":         "PORCELANATO_60X60",
    "porcelanato_60x60_premium": "PORCELANATO_60X60_PREMIUM",
    "ceramico_pared_25x35":      "CERAMICO_PARED_25X35",
    "ceramico_30x30":            "CERAMICO_30X30",
    "ceramico_45x45":            "CERAMICO_45X45",
}
ADHESIVO_POR_MAT: dict[str, str] = {
    "porcelanato_60x60":         "ADHESIVO_PORCELANATO",
    "porcelanato_60x60_premium": "ADHESIVO_PORCELANATO",
    "ceramico_pared_25x35":      "ADHESIVO_CERAMICO",
    "ceramico_30x30":            "ADHESIVO_CERAMICO",
    "ceramico_45x45":            "ADHESIVO_CERAMICO",
}
ADHESIVO_M2_POR_BOLSA = Decimal("4")   # cerámico
ADHESIVO_PORCELANATO_M2_POR_BOLSA = Decimal("3")  # porcelanato necesita más adhesivo
JUNTA_M2_POR_KG = Decimal("3")
```

**Lógica `calcular()`:**

Función auxiliar interna `_partidas_superficie(sup_m2, material_key, tarea_mo, descripcion_concepto)` que genera las partidas para una superficie dada:
- Material con 10% desperdicio: `cant = _q(sup_m2 * rend(datos, codigo, Decimal("1.10")))`
- Adhesivo: `cant_adhesivo = ceil(sup_m2 / m2_por_bolsa)`
- Pastina: `cant_pastina = ceil(sup_m2 / JUNTA_M2_POR_KG)`
- Mano de obra: `precio_mano_obra(datos, tarea_mo) * sup_m2`

Llamar `_partidas_superficie` para:
1. Piso (si `superficie_piso_m2 > 0`) — usa tarea `"PISO_CERAMICO"`
2. Paredes (si `superficie_pared_m2 > 0`) — usa tarea `"REVESTIMIENTO_CERAMICO"`
3. Alzada cocina (si `incluye_alzada_cocina and superficie_alzada_m2 > 0`) — mismo material que paredes, misma tarea

Si piso y paredes usan el **mismo material**: consolidar materiales (sumar cantidades) pero mantener MO separada.

```python
# Consolidar: si material_piso == material_pared, sumar cant del material en una sola partida
# Pero mantener partidas de MO separadas (piso vs paredes tienen precio distinto)
```

`metadata` debe incluir: `superficie_piso_m2`, `superficie_pared_m2`, `material_piso`, `material_pared`, `incluye_alzada_cocina`.

`accion = "revestimiento_banio"`. Registrar.

**Tests `tests/rubros/test_revestimiento_banio.py`:**
```python
def test_banio_piso_y_paredes_distinto_material():
    # piso=6m2 porcelanato, paredes=18m2 cerámico 25x35
    r = _calc(superficie_piso_m2=6, superficie_pared_m2=18,
              material_piso="porcelanato_60x60", material_pared="ceramico_pared_25x35")
    assert r.metadata["superficie_piso_m2"] == 6.0
    partidas_mat = [p for p in r.partidas if p.categoria == "material"]
    partidas_mo  = [p for p in r.partidas if p.categoria == "mano_obra"]
    assert len(partidas_mo) == 2  # una para piso, otra para paredes

def test_cocina_con_alzada():
    r = _calc(superficie_piso_m2=10, superficie_pared_m2=8,
              material_piso="porcelanato_60x60", material_pared="ceramico_pared_25x35",
              incluye_alzada_cocina=True, superficie_alzada_m2=2.5)
    assert r.metadata["incluye_alzada_cocina"] is True

def test_sin_superficie_falla():
    with pytest.raises(ValueError):
        ParamsRevestimientoBanio(superficie_piso_m2=0, superficie_pared_m2=0)

def test_invariante_suma_igual_total()
def test_propiedad_idempotencia()  # hypothesis
```

3 casos golden: baño completo, cocina con alzada, solo piso (local comercial).

---

## TAREA 8 — Actualizar Registry y prompts

### `src/rubros/__init__.py`

Reemplazar la línea de imports por:
```python
from src.rubros import (  # noqa: F401
    techo_chapa,
    cubierta_tejas,
    mamposteria,
    losa,
    contrapiso,
    revoque_grueso,
    piso_ceramico,
    revestimiento_banio,
)
```

### `src/orquestador/prompts.py` — `SYSTEM_PROMPT`

Agregar en la sección "Acciones disponibles" (formato idéntico al existente):

```
3. "mamposteria":
   - largo: float (m), alto: float (m)
   - tipo: "hueco_12" | "hueco_18" | "comun"

4. "losa":
   - ancho: float (m), largo: float (m), espesor_cm: float (default 12)

5. "contrapiso":
   - superficie_m2: float, espesor_cm: float (default 8)

6. "revoque_grueso":
   - superficie_m2: float, espesor_cm: float (default 1.5)

7. "cubierta_tejas":
   - ancho: float, largo: float
   - tipo_teja: "ceramica_colonial" | "cemento"
   - pendiente_pct: float (default 30)

8. "revestimiento_banio":
   - superficie_piso_m2: float (0 si no aplica)
   - superficie_pared_m2: float (0 si no aplica)
   - material_piso: "porcelanato_60x60" | "porcelanato_60x60_premium" | "ceramico_30x30" | "ceramico_45x45"
   - material_pared: "porcelanato_60x60" | "porcelanato_60x60_premium" | "ceramico_pared_25x35" | "ceramico_30x30"
   - incluye_alzada_cocina: bool (default false)
   - superficie_alzada_m2: float (default 0)
```

Agregar también ejemplos few-shot para los nuevos rubros en el system prompt.

---

## TAREA 9 — Verificación final

```bash
# Instalar deps
pip install -e ".[dev]"

# Tests unitarios (deben pasar TODOS)
pytest -q

# Golden dataset (debe mostrar todos ✅)
python -m scripts.correr_golden --strict

# Smoke test: crear nueva empresa con el CLI
python -m scripts.nueva_empresa "Estudio Test" --id estudio_test

# Verificar que el nuevo rubro está en el registry
python -c "from src.rubros import REGISTRY; print(list(REGISTRY.keys()))"
# Debe imprimir: ['techo_chapa', 'cubierta_tejas', 'mamposteria', 'losa', 'contrapiso', 'revoque_grueso', 'piso_ceramico', 'revestimiento_banio']
```

Si algún test golden falla por precio incorrecto, corregir el `esperado.total` en `casos.yaml` con el cálculo manual. **No cambiar las fórmulas para que el test pase.**

Hacer commit final:
```
feat: Fase 2 — rubros mampostería, losa, contrapiso, revoque, tejas, revestimientos + two-stage routing
```

---

## Notas de dominio importantes (NO ignorar)

- **Plastificante**: Hercal o Plasticor (son lo mismo). Código: `PLASTIFICANTE_HERCAL`. Se usa en mampostería, losa y revoques. **Cal hidráulica eliminada.**
- **Revestimiento baño/cocina**: piso y paredes pueden ser materiales distintos. El rubro `revestimiento_banio` maneja ambos en una sola llamada.
- **Alzada de cocina**: es el zócalo alto de la mesada. Parámetro opcional `incluye_alzada_cocina`.
- **Pendiente en tejas**: afecta la superficie real de material — calcular siempre con el factor de pendiente.
- **Decimal, no float**: todo cálculo monetario usa `Decimal`. Ver `_q()` en `techo_chapa.py`.
