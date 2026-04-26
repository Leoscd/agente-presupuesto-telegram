# TAREAS AGENTE — Fase 4: Estructura completa
> **Fecha:** 2026-04-26 | pytest 128/128 ✅ | golden 25/25 ✅
> **Rubros actuales:** contrapiso, cubierta_tejas, instalacion_electrica, instalacion_sanitaria, losa, mamposteria, piso_ceramico, revestimiento_banio, revoque_fino, revoque_grueso, techo_chapa

---

## REGLAS QUE NUNCA SE ROMPEN

1. **Decimal para todo dinero** — nunca `float` en precios ni subtotales.
2. **`_q(v)`** en cada subtotal: `v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
3. **`registrar(CalcXxx())`** al final de cada archivo de rubro.
4. **Importar en `src/rubros/__init__.py`**: `from src.rubros.nuevo_rubro import CalcNuevoRubro  # noqa: F401`
5. **No llamar `materiales_faltantes()` con conceptos** — solo con códigos reales del CSV.
6. **`advertencias=[]`** si no hay advertencias (no dejar referencia a variables inexistentes).
7. **Verificar todo corriendo el snippet de Python** antes de poner el total en golden cases.
8. **Actualizar los CSV de AMBAS empresas**: `empresas/_plantilla/` y `empresas/estudio_ramos/`.

---

## PASO 0 — Agregar materiales y MO a los CSV (hacer PRIMERO)

Agregar al final de `empresas/_plantilla/precios_materiales.csv` **y** `empresas/estudio_ramos/precios_materiales.csv`:

```
HIERRO_6,Hierro nervado 6mm barra 12m,u,4200.00,2026-04-26
ALAMBRE_ATADO,Alambre de atar kg,kg,2800.00,2026-04-26
TABLON_PINO,Tablón de pino 1"x12"x3m,u,5500.00,2026-04-26
PINTURA_LATEX_INT,Pintura látex interior balde 20L,u,48000.00,2026-04-26
PINTURA_LATEX_EXT,Pintura látex exterior balde 20L,u,58000.00,2026-04-26
PINTURA_ESMALTE,Pintura esmalte sintético balde 4L,u,24000.00,2026-04-26
FIJADOR_SELLADOR_4L,Fijador sellador balde 4L,u,18500.00,2026-04-26
LIJA_PAPEL,Lija al agua pliego N120,u,850.00,2026-04-26
PLACA_DURLOCK_12,Placa Durlock 12mm 1.20x2.40m,u,8500.00,2026-04-26
PERFIL_MONTANTE_70,Perfil montante 70mm x 3m,u,3200.00,2026-04-26
PERFIL_SOLERA_70,Perfil solera 70mm x 3m,u,2800.00,2026-04-26
MASILLA_DURLOCK,Masilla para Durlock bolsa 25kg,u,12500.00,2026-04-26
TORNILLO_DURLOCK,Tornillo autoperforante Durlock bolsa 500u,u,8500.00,2026-04-26
MEMBRANA_ASFALTICA,Membrana asfáltica 40kg rollo 10m2,u,28000.00,2026-04-26
MEMBRANA_LIQUIDA,Membrana líquida balde 20kg,u,32000.00,2026-04-26
PERFIL_IPN_120,Perfil IPN 120 barra 12m,u,185000.00,2026-04-26
PINTURA_ANTICORR,Pintura anticorrosiva lata 4L,u,22000.00,2026-04-26
ELECTRODO_E6013,Electrodos E6013 caja 50u,u,12500.00,2026-04-26
```

Agregar al final de `empresas/_plantilla/precios_mano_obra.csv` **y** `empresas/estudio_ramos/precios_mano_obra.csv`:

```
COLUMNA_HORMIGON,Hormigonado y encofrado columnas,m3,95000.00,
VIGA_ENCADENADO,Hormigonado y encofrado vigas y encadenados,m3,85000.00,
FUNDACION,Hormigonado fundaciones,m3,65000.00,
ESCALERA_HORMIGON,Escalera de hormigon armado,u,185000.00,
PINTURA,Pintura interior o exterior por m2,m2,3500.00,
CIELORRASO_DURLOCK,Colocacion cielorraso Durlock,m2,8500.00,
MEMBRANA_IMPERMEAB,Colocacion membrana impermeabilizante,m2,5500.00,
ESTRUCTURA_METALICA,Montaje estructura metalica,ml,18000.00,
```

---

## TAREA 1 — `src/rubros/columna_hormigon.py`

### Parámetros
```python
class ParamsColumnaHormigon(BaseModel):
    seccion: Literal["20x20", "25x25", "30x30", "30x40", "40x40"] = "25x25"
    altura_m: PositiveFloat = Field(..., ge=2.0, le=12.0)
    cantidad: int = Field(1, ge=1, le=100)
```

### Constantes internas
```python
SECCION_M2 = {
    "20x20": Decimal("0.0400"),
    "25x25": Decimal("0.0625"),
    "30x30": Decimal("0.0900"),
    "30x40": Decimal("0.1200"),
    "40x40": Decimal("0.1600"),
}
DIMS_CM = {   # (dim1_cm, dim2_cm) para calcular perímetro de estribo
    "20x20": (20, 20), "25x25": (25, 25), "30x30": (30, 30),
    "30x40": (30, 40), "40x40": (40, 40),
}
```

### Fórmulas paso a paso
```
seccion_m2 = SECCION_M2[params.seccion]
altura     = Decimal(str(params.altura_m))
cantidad   = Decimal(str(params.cantidad))

volumen_m3 = seccion_m2 * altura * cantidad   # en m³

# H21: igual que losa.py
cemento  = Decimal(ceil(volumen_m3 * Decimal("7")))       # bolsas
arena    = _q(volumen_m3 * Decimal("0.45"))                # m3
piedra   = _q(volumen_m3 * Decimal("0.65"))                # m3
plast    = Decimal(max(1, ceil(volumen_m3 / Decimal("5"))))  # bidones

# Hierro 12mm longitudinal — 4 barras por columna corriendo toda la altura
# 1 barra dura 11m útiles (descarte 1m)
cant_barras_12 = Decimal(ceil(params.cantidad * 4 * float(altura) / 11.0))

# Hierro 6mm estribos — 1 cada 20cm de altura
estribos_por_col = ceil(float(altura) / 0.20)
estribos_total   = estribos_por_col * params.cantidad
# Perímetro de cada estribo = 2×(dim1+dim2)/100 + 0.16m (dobleces)
dim1, dim2    = DIMS_CM[params.seccion]
perim_estribo = Decimal(str(2 * (dim1 + dim2) / 100 + 0.16))
ml_hierro6    = Decimal(str(estribos_total)) * perim_estribo
cant_barras_6 = Decimal(ceil(float(ml_hierro6) / 11.0))

# Alambre de atar: 0.5 kg por m³
cant_alambre = _q(volumen_m3 * Decimal("0.5"))

# Tablones encofrado: perímetro externo × altura × cantidad × 1.10
dim1_m, dim2_m = Decimal(str(dim1/100)), Decimal(str(dim2/100))
perim_col   = 2 * (dim1_m + dim2_m)
m2_encofrado = _q(perim_col * altura * cantidad * Decimal("1.10"))
cant_tablones = Decimal(ceil(float(m2_encofrado) / 0.75))  # 1 tablón = 3m×0.25m = 0.75m²

# Mano de obra
p_mo     = precio_mano_obra(datos, "COLUMNA_HORMIGON")
costo_mo = _q(p_mo * volumen_m3)
```

### Partidas a generar (en este orden)
1. `"Cemento portland"` — cant=cemento, unidad="u", cod=CEMENTO_PORTLAND
2. `"Arena gruesa"` — cant=arena, unidad="m3", cod=ARENA_GRUESA
3. `"Piedra partida 6-12mm"` — cant=piedra, unidad="m3", cod=PIEDRA_6_12
4. `"Plastificante Hercal"` — cant=plast, unidad="u", cod=PLASTIFICANTE_HERCAL
5. `"Hierro 12mm longitudinal"` — cant=cant_barras_12, unidad="u", cod=HIERRO_12
6. `"Hierro 6mm estribos"` — cant=cant_barras_6, unidad="u", cod=HIERRO_6
7. `"Alambre de atar"` — cant=cant_alambre, unidad="kg", cod=ALAMBRE_ATADO
8. `"Tablon encofrado"` — cant=cant_tablones, unidad="u", cod=TABLON_PINO
9. `"MO columnas hormigon"` — cant=volumen_m3, unidad="m3", p_u=p_mo, sub=costo_mo, cat=mano_obra

### metadata
```python
{"volumen_m3": float(volumen_m3), "seccion": params.seccion,
 "altura_m": params.altura_m, "cantidad": params.cantidad}
```

---

## TAREA 2 — `src/rubros/viga_encadenado.py`

### Parámetros
```python
class ParamsVigaEncadenado(BaseModel):
    longitud_ml: PositiveFloat
    base_cm: int = Field(20, ge=15, le=50)
    alto_cm: int = Field(30, ge=20, le=60)
    tipo: Literal["encadenado", "viga_dintel"] = "encadenado"
```

### Fórmulas
```
base   = Decimal(str(params.base_cm)) / Decimal("100")
alto   = Decimal(str(params.alto_cm)) / Decimal("100")
long   = Decimal(str(params.longitud_ml))

volumen_m3 = base * alto * long

# H21 dosificación
cemento  = Decimal(ceil(volumen_m3 * Decimal("7")))
arena    = _q(volumen_m3 * Decimal("0.45"))
piedra   = _q(volumen_m3 * Decimal("0.65"))
plast    = Decimal(max(1, ceil(volumen_m3 / Decimal("5"))))

# Hierro 12mm longitudinal: 4 barras corridas (2 arriba + 2 abajo)
cant_barras_12 = Decimal(ceil(float(long) / 11.0) * 4)

# Hierro 6mm estribos: 1 cada 20cm
estribos_total = ceil(float(long) / 0.20)
perim_estribo  = Decimal("2") * (base + alto) + Decimal("0.16")
ml_hierro6     = Decimal(str(estribos_total)) * perim_estribo
cant_barras_6  = Decimal(ceil(float(ml_hierro6) / 11.0))

# Alambre: 0.5 kg/m3
cant_alambre = _q(volumen_m3 * Decimal("0.5"))

# Tablones encofrado: (2×alto + base) × long × 1.10 / 0.75
m2_enc        = _q((2 * alto + base) * long * Decimal("1.10"))
cant_tablones = Decimal(ceil(float(m2_enc) / 0.75))

# MO
p_mo     = precio_mano_obra(datos, "VIGA_ENCADENADO")
costo_mo = _q(p_mo * volumen_m3)
```

### Partidas (mismo orden que columna, reemplazar "MO columnas" por "MO vigas encadenado")

---

## TAREA 3 — `src/rubros/fundacion.py`

### Parámetros
```python
class ParamsFundacion(BaseModel):
    tipo: Literal["zapata_aislada", "viga_fundacion"] = "zapata_aislada"
    # Zapata aislada: largo × ancho × alto × cantidad
    largo_m: PositiveFloat = Field(0.80)
    ancho_m: PositiveFloat = Field(0.80)
    alto_m: float = Field(0.50, ge=0.30, le=1.50)
    cantidad: int = Field(1, ge=1, le=200)
    # Viga de fundación: longitud × base × alto
    longitud_ml: float = Field(0.0, ge=0.0)
    base_cm: int = Field(40, ge=25, le=80)
```

### Fórmulas
```
Si tipo == "zapata_aislada":
    volumen_m3 = Decimal(str(params.largo_m)) * Decimal(str(params.ancho_m)) *
                 Decimal(str(params.alto_m)) * Decimal(str(params.cantidad))

Si tipo == "viga_fundacion":
    volumen_m3 = Decimal(str(params.base_cm)) / 100 *
                 Decimal(str(params.alto_m)) *
                 Decimal(str(params.longitud_ml))

# H21 dosificación (misma que losa y columnas)
cemento = Decimal(ceil(volumen_m3 * Decimal("7")))
arena   = _q(volumen_m3 * Decimal("0.45"))
piedra  = _q(volumen_m3 * Decimal("0.65"))
plast   = Decimal(max(1, ceil(volumen_m3 / Decimal("5"))))

# Hierro 8mm malla: coeficiente 80 kg/m³
# Barra 8mm 12m pesa: 0.395 kg/m × 12m = 4.74 kg/barra
cant_barras_8 = Decimal(ceil(float(volumen_m3) * 80 / 4.74))

# Alambre: 0.5 kg/m3
cant_alambre = _q(volumen_m3 * Decimal("0.5"))

# Fundaciones NO llevan tablones (se hormigona sobre el terreno excavado)

# MO
p_mo     = precio_mano_obra(datos, "FUNDACION")
costo_mo = _q(p_mo * volumen_m3)
```

### Partidas (sin tablones)
1. Cemento, 2. Arena, 3. Piedra, 4. Plastificante, 5. Hierro 8mm, 6. Alambre, 7. MO fundacion

---

## TAREA 4 — `src/rubros/escalera_hormigon.py`

### Parámetros
```python
class ParamsEscaleraHormigon(BaseModel):
    cantidad_escalones: int = Field(..., ge=4, le=30)
    ancho_m: float = Field(1.20, ge=0.80, le=3.0)
    huella_cm: float = Field(28.0, ge=22.0, le=35.0)
    contrahuela_cm: float = Field(18.0, ge=15.0, le=22.0)
```

### Fórmulas
```
n    = params.cantidad_escalones
ancho = Decimal(str(params.ancho_m))
huella_m      = Decimal(str(params.huella_cm)) / Decimal("100")
contrahuela_m = Decimal(str(params.contrahuela_cm)) / Decimal("100")

altura_total_m    = contrahuela_m * Decimal(str(n))
longitud_horiz_m  = huella_m * Decimal(str(n))

# Longitud diagonal de la losa inclinada
import math
long_diagonal = Decimal(str(math.sqrt(
    float(altura_total_m)**2 + float(longitud_horiz_m)**2
)))

espesor_losa = Decimal("0.12")  # 12cm constante

# Volumen losa inclinada
vol_losa = long_diagonal * ancho * espesor_losa

# Volumen escalones (prismas triangulares)
vol_escalones = Decimal("0.5") * huella_m * contrahuela_m * Decimal(str(n)) * ancho

volumen_m3 = _q(vol_losa + vol_escalones)

# H21 dosificación
cemento = Decimal(ceil(volumen_m3 * Decimal("7")))
arena   = _q(volumen_m3 * Decimal("0.45"))
piedra  = _q(volumen_m3 * Decimal("0.65"))
plast   = Decimal(max(1, ceil(volumen_m3 / Decimal("5"))))

# Hierro 8mm: coeficiente 17 barras por m³
cant_barras_8 = Decimal(ceil(float(volumen_m3) * 17))

# Tablones encofrado: losa inferior + laterales
m2_enc        = _q(long_diagonal * ancho * Decimal("2.20"))  # factor 2.2 incluye laterales
cant_tablones = Decimal(ceil(float(m2_enc) / 0.75))

# Alambre: 0.5 kg/m3
cant_alambre = _q(volumen_m3 * Decimal("0.5"))

# MO: precio ESCALERA_HORMIGON es por escalón (u), no por m3
p_mo     = precio_mano_obra(datos, "ESCALERA_HORMIGON")
costo_mo = _q(p_mo * Decimal(str(n)))
```

### Partidas
1. Cemento, 2. Arena, 3. Piedra, 4. Plastificante, 5. Hierro 8mm, 6. Alambre, 7. Tablones encofrado, 8. MO escalera (cantidad=n, unidad="u")

### metadata
```python
{"volumen_m3": float(volumen_m3), "cantidad_escalones": n,
 "altura_total_m": float(altura_total_m), "ancho_m": params.ancho_m}
```

---

## TAREA 5 — `src/rubros/pintura.py`

### Parámetros
```python
class ParamsPintura(BaseModel):
    superficie_m2: PositiveFloat
    tipo: Literal["latex_interior", "latex_exterior", "esmalte_sintetico"] = "latex_interior"
    manos: int = Field(2, ge=1, le=4)
    incluye_fijador: bool = True
```

### Constantes
```python
CODIGO_PINTURA = {
    "latex_interior":  "PINTURA_LATEX_INT",
    "latex_exterior":  "PINTURA_LATEX_EXT",
    "esmalte_sintetico": "PINTURA_ESMALTE",
}
LITROS_POR_BALDE = {
    "latex_interior": Decimal("20"),
    "latex_exterior": Decimal("20"),
    "esmalte_sintetico": Decimal("4"),
}
RENDIMIENTO_L_M2 = Decimal("12")   # 12 m² por litro por mano
RENDIMIENTO_FIJADOR_L_M2 = Decimal("15")  # litros fijador por m²
LITROS_BALDE_FIJADOR = Decimal("4")
```

### Fórmulas
```
sup = Decimal(str(params.superficie_m2))

# Pintura
litros_pintura  = sup * Decimal(str(params.manos)) / RENDIMIENTO_L_M2
cant_baldes_pin = Decimal(ceil(float(litros_pintura) / float(LITROS_POR_BALDE[params.tipo])))

# Fijador (solo si aplica)
if params.incluye_fijador:
    litros_fijador      = sup / RENDIMIENTO_FIJADOR_L_M2
    cant_baldes_fijador = Decimal(ceil(float(litros_fijador) / float(LITROS_BALDE_FIJADOR)))

# Lija: 1 pliego cada 10m²
cant_lija = Decimal(ceil(float(sup) / 10.0))

# MO
p_mo     = precio_mano_obra(datos, "PINTURA")
costo_mo = _q(p_mo * sup)
```

### Partidas
1. `f"Pintura {params.tipo} balde"` — cant=cant_baldes_pin, cod=CODIGO_PINTURA[tipo]
2. `"Fijador sellador balde 4L"` — cant=cant_baldes_fijador (solo si incluye_fijador), cod=FIJADOR_SELLADOR_4L
3. `"Lija pliego N120"` — cant=cant_lija, cod=LIJA_PAPEL
4. `"MO pintura"` — cant=sup, unidad="m2"

---

## TAREA 6 — `src/rubros/cielorraso_durlock.py`

### Parámetros
```python
class ParamsCielorraso(BaseModel):
    superficie_m2: PositiveFloat
    tipo: Literal["simple", "doble"] = "simple"
    con_estructura: bool = True
```

### Constantes
```python
M2_POR_PLACA  = Decimal("2.88")   # 1.20m × 2.40m
ML_MONT_POR_M2 = Decimal("2.50")   # ml de montante por m² (1 cada 40cm)
ML_SOL_POR_M2  = Decimal("0.60")   # ml de solera por m² (perímetro estimado)
M2_POR_BOLSA_MAS = Decimal("20")   # m² de masilla por bolsa
TORN_POR_PLACA   = 25              # tornillos por placa
```

### Fórmulas
```
sup   = Decimal(str(params.superficie_m2))
capas = 2 if params.tipo == "doble" else 1

# Placas
cant_placas = Decimal(ceil(float(sup * Decimal("1.10") / M2_POR_PLACA))) * Decimal(str(capas))

# Perfiles (solo si con_estructura)
if params.con_estructura:
    total_ml_mont  = sup * ML_MONT_POR_M2
    cant_montantes = Decimal(ceil(float(total_ml_mont) / 3.0))  # perfil de 3m
    total_ml_sol   = sup * ML_SOL_POR_M2
    cant_soleras   = Decimal(ceil(float(total_ml_sol) / 3.0))

# Masilla
cant_masilla = Decimal(ceil(float(sup) / float(M2_POR_BOLSA_MAS)))

# Tornillos
cant_torn_total = int(cant_placas) * TORN_POR_PLACA
cant_bolsas_torn = Decimal(ceil(cant_torn_total / 500))  # bolsa de 500u

# MO
p_mo     = precio_mano_obra(datos, "CIELORRASO_DURLOCK")
costo_mo = _q(p_mo * sup)
```

### Partidas
1. `"Placa Durlock 12mm"` — cant=cant_placas, cod=PLACA_DURLOCK_12
2. `"Perfil montante 70mm"` — cant=cant_montantes (solo si con_estructura), cod=PERFIL_MONTANTE_70
3. `"Perfil solera 70mm"` — cant=cant_soleras (solo si con_estructura), cod=PERFIL_SOLERA_70
4. `"Masilla Durlock"` — cant=cant_masilla, cod=MASILLA_DURLOCK
5. `"Tornillos Durlock bolsa"` — cant=cant_bolsas_torn, cod=TORNILLO_DURLOCK
6. `"MO cielorraso Durlock"` — cant=sup, unidad="m2"

---

## TAREA 7 — `src/rubros/membrana_impermeabilizante.py`

### Parámetros
```python
class ParamsMembranaImperm(BaseModel):
    superficie_m2: PositiveFloat
    tipo: Literal["membrana_asfaltica", "liquida"] = "membrana_asfaltica"
    capas: int = Field(2, ge=1, le=3)
```

### Fórmulas
```
sup = Decimal(str(params.superficie_m2))

Si tipo == "membrana_asfaltica":
    # 1 rollo cubre 10m², solapar 15%
    cant_rollos = Decimal(ceil(float(sup * Decimal("1.15") / Decimal("10")))) * Decimal(str(params.capas))
    cod_material = "MEMBRANA_ASFALTICA"
    concepto_mat = "Membrana asfaltica rollo 10m2"

Si tipo == "liquida":
    # 1 kg por m² por capa; balde 20kg
    cant_baldes = Decimal(ceil(float(sup * Decimal(str(params.capas))) / 20.0))
    cod_material = "MEMBRANA_LIQUIDA"
    concepto_mat = "Membrana liquida balde 20kg"

# MO
p_mo     = precio_mano_obra(datos, "MEMBRANA_IMPERMEAB")
costo_mo = _q(p_mo * sup)
```

### Partidas
1. Material (rollo o balde según tipo)
2. `"MO impermeabilizacion"` — cant=sup, unidad="m2"

---

## TAREA 8 — `src/rubros/estructura_metalica.py`

### Parámetros
```python
class ParamsEstructuraMetalica(BaseModel):
    tipo_perfil: Literal["IPN_120"] = "IPN_120"
    longitud_ml: PositiveFloat
    incluye_pintura_anticorrosiva: bool = True
```

> Nota: por ahora solo IPN_120. Se puede expandir fácilmente agregando más Literal values y precios en CSV.

### Fórmulas
```
long  = Decimal(str(params.longitud_ml))
CODIGOS = {"IPN_120": "PERFIL_IPN_120"}
cod_perfil = CODIGOS[params.tipo_perfil]

# Barras de 12m
cant_barras = Decimal(ceil(float(long) / 12.0))

# Pintura anticorrosiva: 0.45 m²/ml de perfil, rendimiento 10 m²/L, lata 4L
if params.incluye_pintura_anticorrosiva:
    m2_perfil   = _q(long * Decimal("0.45"))
    litros_ant  = m2_perfil / Decimal("10")
    cant_latas  = Decimal(ceil(float(litros_ant) / 4.0))

# Electrodos: 3 por metro lineal, caja 50u
cant_cajas_elec = Decimal(ceil(float(long) * 3 / 50))

# MO
p_mo     = precio_mano_obra(datos, "ESTRUCTURA_METALICA")
costo_mo = _q(p_mo * long)
```

### Partidas
1. `f"Perfil {params.tipo_perfil} barra 12m"` — cant=cant_barras, cod=cod_perfil
2. `"Pintura anticorrosiva lata 4L"` — cant=cant_latas (solo si aplica), cod=PINTURA_ANTICORR
3. `"Electrodos E6013 caja 50u"` — cant=cant_cajas_elec, cod=ELECTRODO_E6013
4. `"MO estructura metalica"` — cant=long, unidad="ml"

---

## TAREA 9 — Actualizar `src/rubros/__init__.py`

Agregar al bloque de imports:
```python
from src.rubros import (  # noqa: F401
    ...rubros existentes...,
    columna_hormigon,
    viga_encadenado,
    fundacion,
    escalera_hormigon,
    pintura,
    cielorraso_durlock,
    membrana_impermeabilizante,
    estructura_metalica,
)
```

---

## TAREA 10 — Actualizar `src/rubros/categorias.py`

```python
CATEGORIAS: dict[str, list[str]] = {
    "cubiertas": ["techo_chapa", "cubierta_tejas", "membrana_impermeabilizante"],
    "obra_gruesa": [
        "mamposteria", "losa", "contrapiso",
        "columna_hormigon", "viga_encadenado", "fundacion",
        "escalera_hormigon", "estructura_metalica",
    ],
    "terminaciones": [
        "revoque_grueso", "revoque_fino", "piso_ceramico",
        "revestimiento_banio", "pintura", "cielorraso_durlock",
    ],
    "instalaciones": ["instalacion_electrica", "instalacion_sanitaria"],
}
```

---

## TAREA 11 — Actualizar `src/orquestador/prompts.py`

### En `SYSTEM_PROMPT_CATEGORIA` — ampliar descripción de obra_gruesa:
```
- obra_gruesa: mampostería, losa, contrapiso, columnas, vigas, encadenados, fundaciones, escaleras, estructura metálica
- terminaciones: revoques, pisos, cerámicos, porcelanato, revestimientos, pintura, durlock, cielorraso
```

### En `SYSTEM_PROMPT` — agregar al bloque ACCIONES DISPONIBLES (continuar numeración desde 11):

```
12. "columna_hormigon": seccion("20x20"|"25x25"|"30x30"|"30x40"|"40x40", default "25x25"), altura_m, cantidad(default 1)

13. "viga_encadenado": longitud_ml, base_cm(default 20), alto_cm(default 30), tipo("encadenado"|"viga_dintel", default "encadenado")

14. "fundacion": tipo("zapata_aislada"|"viga_fundacion", default "zapata_aislada"), largo_m(default 0.80), ancho_m(default 0.80), alto_m(default 0.50), cantidad(default 1), longitud_ml(default 0), base_cm(default 40)

15. "escalera_hormigon": cantidad_escalones, ancho_m(default 1.20), huella_cm(default 28), contrahuela_cm(default 18)

16. "pintura": superficie_m2, tipo("latex_interior"|"latex_exterior"|"esmalte_sintetico", default "latex_interior"), manos(default 2), incluye_fijador(bool, default true)

17. "cielorraso_durlock": superficie_m2, tipo("simple"|"doble", default "simple"), con_estructura(bool, default true)

18. "membrana_impermeabilizante": superficie_m2, tipo("membrana_asfaltica"|"liquida", default "membrana_asfaltica"), capas(default 2)

19. "estructura_metalica": tipo_perfil("IPN_120", default "IPN_120"), longitud_ml, incluye_pintura_anticorrosiva(bool, default true)
```

### Agregar EJEMPLOS al final del bloque EJEMPLOS:
```
USUARIO: "8 columnas de 25x25 de 3 metros"
SALIDA: {"accion":"columna_hormigon","parametros":{"seccion":"25x25","altura_m":3,"cantidad":8},"confianza":0.95}

USUARIO: "encadenado superior 40 metros lineales sección 20x30"
SALIDA: {"accion":"viga_encadenado","parametros":{"longitud_ml":40,"base_cm":20,"alto_cm":30,"tipo":"encadenado"},"confianza":0.95}

USUARIO: "pintura latex interior 120m2 dos manos"
SALIDA: {"accion":"pintura","parametros":{"superficie_m2":120,"tipo":"latex_interior","manos":2,"incluye_fijador":true},"confianza":0.97}

USUARIO: "cielorraso durlock simple 45m2"
SALIDA: {"accion":"cielorraso_durlock","parametros":{"superficie_m2":45,"tipo":"simple","con_estructura":true},"confianza":0.95}

USUARIO: "membrana asfaltica losa de 30m2"
SALIDA: {"accion":"membrana_impermeabilizante","parametros":{"superficie_m2":30,"tipo":"membrana_asfaltica","capas":2},"confianza":0.95}

USUARIO: "escalera hormigon 12 escalones ancho 1.20"
SALIDA: {"accion":"escalera_hormigon","parametros":{"cantidad_escalones":12,"ancho_m":1.20,"huella_cm":28,"contrahuela_cm":18},"confianza":0.93}
```

---

## TAREA 12 — Tests unitarios

Crear un archivo de tests por rubro. Modelo: `tests/rubros/test_techo_chapa.py`.

### `tests/rubros/test_columna_hormigon.py`
```python
def test_8_columnas_25x25_3m():
    r = _calc(seccion="25x25", altura_m=3, cantidad=8)
    # vol = 0.0625 × 3 × 8 = 1.50 m³
    assert r.metadata["volumen_m3"] == pytest.approx(1.50, abs=0.01)
    assert r.total > 0
    assert sum(p.subtotal for p in r.partidas) == r.total

def test_invariante_suma():
    r = _calc(seccion="30x30", altura_m=4, cantidad=4)
    assert sum(p.subtotal for p in r.partidas) == r.total

def test_cantidad_hierro_12_correcta():
    # 4 barras × 4 columnas × 4m / 11m = ceil(5.81) = 6 barras
    r = _calc(seccion="25x25", altura_m=4, cantidad=4)
    h12 = next(p for p in r.partidas if "12mm" in p.concepto)
    assert h12.cantidad == Decimal("6")
```

### `tests/rubros/test_viga_encadenado.py`
```python
def test_encadenado_40ml_20x30():
    r = _calc(longitud_ml=40, base_cm=20, alto_cm=30)
    # vol = 0.20 × 0.30 × 40 = 2.40 m³
    assert r.metadata["volumen_m3"] == pytest.approx(2.40, abs=0.01)
    assert sum(p.subtotal for p in r.partidas) == r.total

def test_hierro_longitudinal():
    # 40ml / 11 = ceil(3.63) = 4 × 4 barras = 16 barras de 12mm
    r = _calc(longitud_ml=40, base_cm=20, alto_cm=30)
    h12 = next(p for p in r.partidas if "12mm" in p.concepto)
    assert h12.cantidad == Decimal("16")
```

### `tests/rubros/test_pintura.py`
```python
def test_pintura_latex_120m2_2manos():
    r = _calc(superficie_m2=120, tipo="latex_interior", manos=2)
    # litros = 120×2/12 = 20L → 1 balde de 20L
    pintura = next(p for p in r.partidas if "latex" in p.concepto.lower())
    assert pintura.cantidad == Decimal("1")
    assert sum(p.subtotal for p in r.partidas) == r.total

def test_incluye_fijador():
    r = _calc(superficie_m2=60, incluye_fijador=True)
    assert any("fijador" in p.concepto.lower() for p in r.partidas)

def test_sin_fijador():
    r = _calc(superficie_m2=60, incluye_fijador=False)
    assert not any("fijador" in p.concepto.lower() for p in r.partidas)
```

### `tests/rubros/test_escalera_hormigon.py`
```python
def test_escalera_12_escalones():
    r = _calc(cantidad_escalones=12, ancho_m=1.20)
    assert r.metadata["cantidad_escalones"] == 12
    assert r.total > 0
    assert sum(p.subtotal for p in r.partidas) == r.total

def test_mo_por_escalon_no_por_m3():
    # La MO tiene unidad "u" (escalon), no m3
    mo = next(p for p in r.partidas if p.categoria == "mano_obra")
    assert mo.unidad == "u"
```

### Para los demás rubros: al menos 3 tests cada uno:
- `test_invariante_suma_partidas()` — siempre
- `test_caso_base()` — con valores concretos y total > 0
- `test_propiedad_idempotencia()` con hypothesis

---

## TAREA 13 — Golden cases

Agregar al final de `tests/golden/casos.yaml`.

**IMPORTANTE: calcular el total corriendo Python antes de escribirlo en el YAML.**

```bash
python -c "
import src.rubros
from src.orquestador.router import despachar

casos = [
    ('columna_hormigon', {'seccion': '25x25', 'altura_m': 3, 'cantidad': 8}),
    ('viga_encadenado',  {'longitud_ml': 40, 'base_cm': 20, 'alto_cm': 30}),
    ('fundacion',        {'tipo': 'zapata_aislada', 'largo_m': 0.80, 'ancho_m': 0.80, 'alto_m': 0.50, 'cantidad': 10}),
    ('escalera_hormigon',{'cantidad_escalones': 12, 'ancho_m': 1.20}),
    ('pintura',          {'superficie_m2': 120, 'tipo': 'latex_interior', 'manos': 2}),
    ('cielorraso_durlock',{'superficie_m2': 45}),
    ('membrana_impermeabilizante', {'superficie_m2': 30, 'tipo': 'membrana_asfaltica'}),
    ('estructura_metalica', {'tipo_perfil': 'IPN_120', 'longitud_ml': 24}),
]
for accion, params in casos:
    r = despachar(accion, params, 'estudio_ramos')
    print(f'{accion}: {r.total}')
"
```

Formato de cada caso:
```yaml
- id: col_001
  descripcion: "8 columnas 25x25 de 3m altura"
  empresa: estudio_ramos
  fecha_precios: 2026-04-26
  accion: columna_hormigon
  parametros:
    seccion: "25x25"
    altura_m: 3
    cantidad: 8
  esperado:
    total: <VALOR_CALCULADO>  # reemplazar con el número real
```

---

## VERIFICACIÓN FINAL

Correr antes de hacer commit:

```bash
# 1. Tests
.venv\Scripts\python -m pytest tests/ -v

# 2. Golden
PYTHONPATH=. .venv\Scripts\python scripts/correr_golden.py

# 3. Smoke test pipeline MiniMax (requiere internet)
.venv\Scripts\python -c "
import asyncio, src.rubros
from src.persistencia.db import init_db; init_db()
from src.orquestador.minimax_client import parsear
from src.orquestador.router import despachar
from src.datos.loader import cargar_empresa

async def t():
    textos = [
        '8 columnas de 25x25 de 3 metros',
        'encadenado superior 40ml seccion 20x30',
        'pintura latex interior 120m2',
        'cielorraso durlock simple 45m2',
    ]
    for txt in textos:
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

## NOTAS PARA EL AGENTE

- El patrón H21 (cemento×7, arena×0.45, piedra×0.65, plastificante cada 5m³) es **idéntico** en columnas, vigas, fundaciones y escaleras. Copialo de `losa.py` y ajustá solo el volumen.
- Los imports de cada rubro siempre: `cargar_empresa, precio_mano_obra, precio_material` de `src.datos.loader`, y `Partida, ResultadoPresupuesto, registrar` de `src.rubros.base`.
- Nunca importar `materiales_faltantes` a menos que se use con códigos reales de CSV.
- La función `registrar()` recibe una **instancia**, no la clase: `registrar(CalcColumnaHormigon())`.
