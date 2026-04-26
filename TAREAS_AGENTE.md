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

## TAREA 14 — Actualización de precios por lenguaje natural

### Objetivo
Cuando el usuario diga *"el cemento ahora vale $7200"*, *"mano de obra pintura: $3800/m2"* o *"CERAMICO_45X45 cuesta $4500"*, el bot debe actualizar el CSV de la empresa y confirmar el cambio.

**Seguridad:** solo usuarios admin pueden actualizar precios. Verificar con `auth.es_admin(user_id)` antes de ejecutar.

---

### PASO A — Agregar función `actualizar_precio_material` en `src/datos/loader.py`

Agregar al final del archivo (antes de nada, agregar `from datetime import date` al bloque de imports):

```python
def actualizar_precio_material(empresa_id: str, codigo: str, nuevo_precio: Decimal) -> Decimal:
    """Edita precio en precios_materiales.csv. Devuelve precio anterior.
    El hot-reload es automático: mtime cambia → próxima llamada a cargar_empresa() recarga.
    """
    from datetime import date
    d = _empresa_dir(empresa_id)
    path = d / "precios_materiales.csv"
    df = pd.read_csv(path, dtype={"codigo": str, "descripcion": str, "unidad": str})
    mask = df["codigo"] == codigo.upper()
    if not mask.any():
        # intento case-insensitive sobre descripcion
        mask = df["descripcion"].str.upper() == codigo.upper()
        if not mask.any():
            raise MaterialNoEncontrado(f"Código '{codigo}' no encontrado en materiales de {empresa_id}")
    precio_anterior = Decimal(str(df.loc[mask, "precio"].iloc[0]))
    df.loc[mask, "precio"] = float(nuevo_precio)
    df.loc[mask, "fecha_actualizacion"] = date.today().isoformat()
    df.to_csv(path, index=False)
    return precio_anterior


def actualizar_precio_mano_obra(empresa_id: str, tarea: str, nuevo_precio: Decimal) -> Decimal:
    """Edita precio en precios_mano_obra.csv. Devuelve precio anterior."""
    d = _empresa_dir(empresa_id)
    path = d / "precios_mano_obra.csv"
    df = pd.read_csv(path, dtype={"tarea": str, "descripcion": str, "unidad": str})
    mask = df["tarea"] == tarea.upper()
    if not mask.any():
        mask = df["descripcion"].str.upper().str.contains(tarea.upper(), na=False)
        if not mask.any():
            raise MaterialNoEncontrado(f"Tarea '{tarea}' no encontrada en MO de {empresa_id}")
    precio_anterior = Decimal(str(df.loc[mask, "precio"].iloc[0]))
    df.loc[mask, "precio"] = float(nuevo_precio)
    df.to_csv(path, index=False)
    return precio_anterior


def listar_materiales_con_descripcion(empresa_id: str) -> list[dict]:
    """Devuelve lista [{codigo, descripcion, unidad, precio}] para pasar a MiniMax."""
    datos = cargar_empresa(empresa_id)
    return [
        {
            "codigo": str(r["codigo"]),
            "descripcion": str(r["descripcion"]),
            "unidad": str(r["unidad"]),
            "precio_actual": float(r["precio"]),
        }
        for _, r in datos.precios_materiales.iterrows()
    ]


def listar_mo_con_descripcion(empresa_id: str) -> list[dict]:
    """Devuelve lista [{tarea, descripcion, unidad, precio}] para pasar a MiniMax."""
    datos = cargar_empresa(empresa_id)
    return [
        {
            "tarea": str(r["tarea"]),
            "descripcion": str(r["descripcion"]),
            "unidad": str(r["unidad"]),
            "precio_actual": float(r["precio"]),
        }
        for _, r in datos.precios_mano_obra.iterrows()
    ]
```

---

### PASO B — Nuevas acciones en `src/orquestador/prompts.py`

Agregar al SYSTEM_PROMPT, en la sección ACCIONES DISPONIBLES (después de la acción 11):

```
12. "actualizar_precio": codigo_material(str — código del CSV en mayúsculas), nuevo_precio(float), descripcion_usuario(str — lo que dijo el usuario)
    → cuando el usuario informa un precio nuevo para un MATERIAL (cemento, hierro, cerámica, etc.)
    → mapeá el nombre coloquial al código CSV más cercano en la lista de materiales
    → EJEMPLO: "el cemento subió a 7200" → {"accion":"actualizar_precio","parametros":{"codigo_material":"CEMENTO_PORTLAND","nuevo_precio":7200,"descripcion_usuario":"cemento"},"confianza":0.92}

13. "actualizar_mano_obra": codigo_tarea(str — código del CSV en mayúsculas), nuevo_precio(float), descripcion_usuario(str)
    → cuando el usuario informa un precio nuevo para MANO DE OBRA (colocación, hormigonado, etc.)
    → EJEMPLO: "mano de obra pintura ahora $3800/m2" → {"accion":"actualizar_mano_obra","parametros":{"codigo_tarea":"PINTURA","nuevo_precio":3800,"descripcion_usuario":"mano de obra pintura"},"confianza":0.90}
```

Agregar ejemplos al final de EJEMPLOS:
```
USUARIO: "el cemento portland subió a $7500 la bolsa"
SALIDA: {"accion":"actualizar_precio","parametros":{"codigo_material":"CEMENTO_PORTLAND","nuevo_precio":7500,"descripcion_usuario":"cemento portland"},"confianza":0.95}

USUARIO: "mano de obra colocación cerámico: $3200 el m2"
SALIDA: {"accion":"actualizar_mano_obra","parametros":{"codigo_tarea":"PISO_CERAMICO","nuevo_precio":3200,"descripcion_usuario":"colocación cerámico"},"confianza":0.91}
```

Agregar nueva función `build_user_message_precio()`:
```python
def build_user_message_precio(
    texto_usuario: str,
    materiales: list[dict],
    mano_obra: list[dict],
) -> str:
    """Mensaje con catálogo completo para que MiniMax mapee nombre → código CSV."""
    ctx = {
        "materiales": materiales,   # [{codigo, descripcion, unidad, precio_actual}]
        "mano_obra": mano_obra,     # [{tarea, descripcion, unidad, precio_actual}]
    }
    return (
        f"Catálogo de la empresa:\n{json.dumps(ctx, ensure_ascii=False)}\n\n"
        f"Mensaje del arquitecto:\n{texto_usuario.strip()}"
    )
```

---

### PASO C — Nueva función `parsear_precio()` en `src/orquestador/minimax_client.py`

```python
async def parsear_precio(texto_usuario: str, materiales: list[dict], mano_obra: list[dict]) -> RespuestaOrq:
    """NLU para actualización de precios. Pasa catálogo completo para mapear códigos."""
    from src.orquestador.prompts import build_user_message_precio
    t0 = time.perf_counter()
    user_msg = build_user_message_precio(texto_usuario, materiales, mano_obra)
    resp: ChatCompletion = await _cliente().chat.completions.create(
        model=settings.minimax_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=500,
    )
    latencia_ms = int((time.perf_counter() - t0) * 1000)
    content = _strip_think(resp.choices[0].message.content or "{}")
    try:
        raw = json.loads(content)
    except json.JSONDecodeError:
        raw = {"accion": "aclaracion", "parametros": {"pregunta": "No entendí el precio. ¿Me das el código y el valor?"}, "confianza": 0.0}
    usage = resp.usage
    tin = usage.prompt_tokens if usage else 0
    tout = usage.completion_tokens if usage else 0
    usd = _estimar_usd(tin, tout)
    db.acumular_tokens(tin, tout, usd)
    return RespuestaOrq(
        accion=str(raw.get("accion", "")),
        parametros=dict(raw.get("parametros", {})),
        confianza=float(raw.get("confianza", 0.0)),
        raw=raw,
        tokens_input=tin,
        tokens_output=tout,
        usd_estimado=usd,
        latencia_ms=latencia_ms,
    )
```

---

### PASO D — Handler en `src/bot/handlers.py`

1. Agregar imports al inicio:
```python
from decimal import Decimal, InvalidOperation
from src.datos.loader import (
    actualizar_precio_material,
    actualizar_precio_mano_obra,
    listar_materiales_con_descripcion,
    listar_mo_con_descripcion,
)
from src.orquestador.minimax_client import parsear_precio
```

2. En `on_mensaje()`, **después** del bloque de confianza baja (paso 2) y **antes** del bloque de cálculo (paso 3), insertar:

```python
    # 2b) Actualización de precio (solo admin)
    if resp.accion in ("actualizar_precio", "actualizar_mano_obra"):
        if not auth.es_admin(user_id):
            await update.message.reply_text("⛔ Solo el admin puede actualizar precios.")
            return
        params = resp.parametros
        try:
            nuevo_precio = Decimal(str(params.get("nuevo_precio", 0)))
            if nuevo_precio <= 0:
                raise InvalidOperation
        except InvalidOperation:
            await update.message.reply_text("No pude leer el precio. Escribilo como número, ej: `7200`")
            return

        try:
            if resp.accion == "actualizar_precio":
                codigo = str(params.get("codigo_material", "")).upper()
                precio_anterior = actualizar_precio_material(empresa_id, codigo, nuevo_precio)
                await update.message.reply_text(
                    f"✅ *{codigo}* actualizado\n"
                    f"Precio anterior: ${float(precio_anterior):,.2f}\n"
                    f"Precio nuevo: ${float(nuevo_precio):,.2f}",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                tarea = str(params.get("codigo_tarea", "")).upper()
                precio_anterior = actualizar_precio_mano_obra(empresa_id, tarea, nuevo_precio)
                await update.message.reply_text(
                    f"✅ MO *{tarea}* actualizada\n"
                    f"Precio anterior: ${float(precio_anterior):,.2f}\n"
                    f"Precio nuevo: ${float(nuevo_precio):,.2f}",
                    parse_mode=ParseMode.MARKDOWN,
                )
        except Exception as e:
            await update.message.reply_text(f"❌ No pude actualizar: {e}")
        return
```

3. En `on_mensaje()`, la detección de intención de actualizar precio debe ocurrir **antes** de llamar a `parsear()` normal. Reemplazar el bloque NLU (paso 1) con:

```python
    # 1) Detectar si es actualización de precio ANTES de llamar al NLU general
    _PRECIO_RE = re.compile(
        r"\b(precio|vale|cuesta|subió|bajó|actualiz|tarifa|mano.?de.?obra)\b",
        re.IGNORECASE
    )
    if auth.es_admin(user_id) and _PRECIO_RE.search(texto):
        # Usar NLU especial con catálogo completo
        await update.message.chat.send_action(action="typing")
        try:
            mats = listar_materiales_con_descripcion(empresa_id)
            mos = listar_mo_con_descripcion(empresa_id)
            resp = await parsear_precio(texto, mats, mos)
        except Exception as e:
            log.exception("Error MiniMax parsear_precio")
            await update.message.reply_text(f"Error: {e}")
            return
        # Si MiniMax reconoció una acción de precio, el bloque 2b la maneja.
        # Si devolvió otro tipo de acción (ej. techo_chapa), caer al flujo normal.
        if resp.accion in ("actualizar_precio", "actualizar_mano_obra", "aclaracion"):
            # bloque 2b se encarga abajo
            pass
        else:
            # No era precio, continuar con resp ya cargado (skip NLU general)
            pass
    else:
        # 1) NLU estándar
        await update.message.chat.send_action(action="typing")
        try:
            resp = await minimax_client.parsear(texto, datos.materiales_disponibles)
        except Exception as e:
            log.exception("Error MiniMax")
            await update.message.reply_text(f"Error consultando el orquestador: {e}")
            return
```

**Importante:** agregar `import re` al inicio de `handlers.py` si no está ya.

---

### PASO E — Tests para TAREA 14

Crear `tests/test_precio_update.py`:

```python
"""Tests para actualización de precios por lenguaje natural."""
import shutil
from decimal import Decimal
from pathlib import Path
import pytest
from src.datos.loader import actualizar_precio_material, actualizar_precio_mano_obra, cargar_empresa

EMPRESA = "estudio_ramos"

def test_actualizar_precio_material(tmp_path):
    # Crear empresa temporal copiando estudio_ramos
    empresa_tmp = tmp_path / "empresa_test"
    shutil.copytree(Path("empresas/estudio_ramos"), empresa_tmp)
    # Patch settings para usar tmp
    # ... (usar monkeypatch de pytest para settings.data_dir)
    # Verificar que el precio cambió

def test_actualizar_precio_material_codigo_no_existe():
    with pytest.raises(Exception, match="no encontrado"):
        actualizar_precio_material(EMPRESA, "MATERIAL_INVENTADO_XYZ", Decimal("1000"))

def test_actualizar_precio_mano_obra_codigo_no_existe():
    with pytest.raises(Exception, match="no encontrada"):
        actualizar_precio_mano_obra(EMPRESA, "TAREA_INVENTADA_XYZ", Decimal("1000"))
```

---

## TAREA 15 — Cotización por imagen (visión)

### Objetivo
El arquitecto envía una foto de:
- Un **sketch/plano con medidas** a mano alzada (techo 7×10, perfil C100)
- Una **foto de una fachada** con dimensiones anotadas
- Un **plano de baño** con cotas
- Una **lista de precios** escaneada o fotografiada

El bot interpreta la imagen y devuelve el mismo presupuesto que si el usuario hubiera escrito el pedido en texto.

---

### PASO A — Función `parsear_imagen()` en `src/orquestador/minimax_client.py`

**Cómo funciona:** MiniMax-M2 soporta input multimodal (imagen + texto) vía el mismo endpoint OpenAI-compatible. Se envía la imagen como `image_url` con base64.

```python
import base64

SYSTEM_PROMPT_VISION = """Sos el parser NLU de un bot de presupuestos de obra para arquitectos argentinos.
Analizá la imagen y extraé la información necesaria para presupuestar.

La imagen puede ser:
- Un sketch o croquis con medidas (ej: techo 7x10m, perfil C100)
- Una foto de un plano arquitectónico con cotas
- Una foto de un ambiente con dimensiones
- Una lista de precios o presupuesto existente

Tu tarea: devolver el mismo JSON que si el usuario hubiera escrito el pedido en texto.

""" + SYSTEM_PROMPT  # reutiliza todas las acciones y reglas


async def parsear_imagen(
    foto_bytes: bytes,
    materiales_disponibles: list[str],
    mime_type: str = "image/jpeg",
) -> RespuestaOrq:
    """NLU sobre imagen. Convierte foto en base64 y llama a MiniMax con vision."""
    t0 = time.perf_counter()

    b64 = base64.b64encode(foto_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    ctx_text = (
        f"Materiales disponibles en la empresa: {materiales_disponibles}\n\n"
        "Analizá la imagen y devolvé el JSON de presupuesto."
    )

    resp: ChatCompletion = await _cliente().chat.completions.create(
        model=settings.minimax_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_VISION},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ctx_text},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1000,
    )

    latencia_ms = int((time.perf_counter() - t0) * 1000)
    content = _strip_think(resp.choices[0].message.content or "{}")
    try:
        raw = json.loads(content)
    except json.JSONDecodeError:
        raw = {
            "accion": "aclaracion",
            "parametros": {"pregunta": "No pude interpretar la imagen. ¿Podés escribir las dimensiones?"},
            "confianza": 0.0,
        }

    usage = resp.usage
    tin = usage.prompt_tokens if usage else 0
    tout = usage.completion_tokens if usage else 0
    usd = _estimar_usd(tin, tout)
    db.acumular_tokens(tin, tout, usd)

    return RespuestaOrq(
        accion=str(raw.get("accion", "")),
        parametros=dict(raw.get("parametros", {})),
        confianza=float(raw.get("confianza", 0.0)),
        raw=raw,
        tokens_input=tin,
        tokens_output=tout,
        usd_estimado=usd,
        latencia_ms=latencia_ms,
    )
```

---

### PASO B — Handler de foto en `src/bot/handlers.py`

1. Agregar el import al inicio:
```python
from src.orquestador.minimax_client import parsear_imagen
```

2. Agregar la función handler:

```python
async def on_foto(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para mensajes con imagen. Misma lógica que on_mensaje pero vía visión."""
    if update.effective_user is None or update.message is None:
        return
    if not update.message.photo:
        return

    user_id = update.effective_user.id
    try:
        empresa_id = auth.resolver_empresa(user_id)
    except PermissionError as e:
        await update.message.reply_text(str(e))
        return

    datos = cargar_empresa(empresa_id)

    # Descargar la foto (mayor resolución disponible = último elemento)
    foto = update.message.photo[-1]
    await update.message.chat.send_action(action="typing")
    foto_file = await _ctx.bot.get_file(foto.file_id)
    foto_bytes = await foto_file.download_as_bytearray()

    # Texto adicional que el usuario haya escrito junto con la foto (caption)
    caption = update.message.caption or ""
    if caption:
        await update.message.reply_text(f"📸 Imagen recibida. Analizando con nota: *{caption}*", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("📸 Imagen recibida. Analizando dimensiones y materiales...")

    try:
        resp = await parsear_imagen(bytes(foto_bytes), datos.materiales_disponibles)
    except Exception as e:
        log.exception("Error MiniMax visión")
        await update.message.reply_text(f"No pude procesar la imagen: {e}")
        return

    log.info("VISION NLU: %s (conf=%.2f, tokens=%d/%d, $%.5f)",
             resp.accion, resp.confianza, resp.tokens_input, resp.tokens_output, resp.usd_estimado)

    # Si el caption tiene info adicional, combinar con lo extraído de la imagen
    # (el arquitecto puede escribir "techo" y la imagen tiene las medidas)
    if caption and resp.accion == "aclaracion":
        # Reintentar con texto + contexto de imagen fallida
        await update.message.reply_text(
            "No pude leer las medidas de la imagen. ¿Me las escribís en texto?\n"
            "Ej: `techo chapa 7x10 perfil C100`"
        )
        return

    # Desde acá, flujo idéntico a on_mensaje (pasos 2→7)
    if resp.accion == "aclaracion":
        pregunta = resp.parametros.get("pregunta", "No pude leer las medidas. ¿Me las escribís?")
        await update.message.reply_text(f"❓ {pregunta}")
        return

    if resp.confianza < CONFIANZA_MIN:
        await update.message.reply_text(
            f"Vi algo en la imagen pero no estoy seguro (confianza {resp.confianza:.0%}).\n"
            f"Interpreté: {resp.accion} con parámetros {resp.parametros}.\n"
            "¿Es correcto o me confirmás las medidas?"
        )
        return

    try:
        resultado = router.despachar(resp.accion, resp.parametros, empresa_id)
    except router.AccionDesconocida as e:
        await update.message.reply_text(f"No tengo calculadora para eso todavía. {e}")
        return
    except ValueError as e:
        await update.message.reply_text(f"No pude calcular: {e}")
        return

    mediana = db.mediana_total(empresa_id, resultado.rubro)
    if mediana and float(resultado.total) > mediana * OUTLIER_FACTOR:
        resultado.advertencias.append(
            f"Total {float(resultado.total)/mediana:.0%} por encima de la mediana. Revisá medidas."
        )

    pid, id_corto = db.guardar_presupuesto(
        empresa_id=empresa_id,
        telegram_user_id=user_id,
        input_texto=f"[imagen] {caption}",
        minimax_json=resp.raw,
        minimax_confianza=resp.confianza,
        resultado=resultado,
        tokens_input=resp.tokens_input,
        tokens_output=resp.tokens_output,
        usd_estimado=resp.usd_estimado,
        latencia_ms=resp.latencia_ms,
    )

    texto_ok = formatter.formatear_presupuesto(resultado, id_corto)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Generar PDF", callback_data=f"pdf:{pid}")],
        [
            InlineKeyboardButton("✅ Preciso", callback_data=f"fb_ok:{pid}"),
            InlineKeyboardButton("❌ Corregir", callback_data=f"fb_bad:{pid}"),
        ],
    ])
    await update.message.reply_text(texto_ok, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb)
```

3. En `registrar(app)`, agregar el handler de foto:
```python
app.add_handler(MessageHandler(filters.PHOTO, on_foto))
```
**Ponerlo ANTES** del handler de texto para que las fotos no caigan en `on_mensaje`.

---

### PASO C — Manejo del caso mixto: imagen + lista de precios

Si el arquitecto manda una foto de una **lista de precios** (foto de revista, proveedor, etc.), el bot debe detectarlo y usar el flujo de `parsear_precio` en lugar del flujo de cotización.

En `on_foto()`, antes de llamar a `parsear_imagen()`, agregar detección por caption:

```python
    # Detectar si la imagen es una lista de precios (caption lo indica)
    _LISTA_PRECIOS_RE = re.compile(
        r"\b(precio|lista.?precio|cotiz|proveedor|actualiz|material|tarifa)\b",
        re.IGNORECASE
    )
    if auth.es_admin(user_id) and caption and _LISTA_PRECIOS_RE.search(caption):
        # Imagen de lista de precios: usar parsear_imagen con prompt especializado
        # Por ahora: pedir confirmación manual de cada precio extraído
        await update.message.reply_text(
            "📋 Veo que es una lista de precios. Extraigo los valores...\n"
            "_Esta función actualiza automáticamente los materiales que reconozca._",
            parse_mode=ParseMode.MARKDOWN,
        )
        # parsear_imagen con SYSTEM_PROMPT_VISION manejará el caso —
        # si MiniMax devuelve accion="actualizar_precio", el bloque 2b lo aplica
        # Si devuelve múltiples precios, necesitaríamos un nuevo tipo de acción:
        # "actualizar_multiples_precios": lista de {codigo, precio}
        # (implementar en iteración futura — por ahora informar que se actualiza de a uno)
        await update.message.reply_text(
            "💡 Por ahora actualizá de a un precio a la vez escribiendo:\n"
            "`el ceramico 45x45 ahora vale $4800`"
        )
        return
```

---

### PASO D — SYSTEM_PROMPT_CATEGORIA actualizado

Agregar al `SYSTEM_PROMPT_CATEGORIA` las nuevas categorías:

```python
SYSTEM_PROMPT_CATEGORIA = """Clasificá el pedido en UNA de estas categorías:
- cubiertas: techos de chapa, tejas, membrana, losa de cubierta
- obra_gruesa: mampostería, losa entre pisos, contrapiso, encadenados
- terminaciones: revoques, pisos, cerámicos, porcelanato, revestimientos
- instalaciones: electricidad, sanitaria, gas
- estructura: columnas, vigas, fundaciones, escaleras de hormigón, estructura metálica
- terminaciones_especiales: pintura, cielorraso, durlock, membrana impermeabilizante
- gestion: actualización de precios, consulta de materiales, historial

Devolvé SOLO JSON: {"categoria": "<nombre>", "confianza": <0.0-1.0>}"""
```

---

### PASO E — Fallback si MiniMax no soporta visión

MiniMax-M2 soporta imágenes vía OpenAI-compatible API. Pero si la llamada falla con error de tipo "model does not support vision" o similar, el handler debe degradar gracefully:

```python
    try:
        resp = await parsear_imagen(bytes(foto_bytes), datos.materiales_disponibles)
    except Exception as e:
        err_str = str(e).lower()
        if "vision" in err_str or "image" in err_str or "multimodal" in err_str:
            await update.message.reply_text(
                "📸 Recibí la imagen, pero el modelo configurado no soporta visión.\n"
                "Escribime las medidas en texto:\n"
                "`techo chapa 7x10 perfil C100`"
            )
        else:
            await update.message.reply_text(f"Error procesando imagen: {e}")
        return
```

---

### PASO F — Tests para TAREA 15

Crear `tests/test_vision.py`:

```python
"""Tests para handler de imágenes (mock de MiniMax vision)."""
import pytest
from unittest.mock import AsyncMock, patch
from src.orquestador.minimax_client import parsear_imagen, RespuestaOrq

@pytest.mark.asyncio
async def test_parsear_imagen_devuelve_respuesta_orq():
    """parsear_imagen() con mock de la API devuelve RespuestaOrq bien formada."""
    mock_resp = {
        "accion": "techo_chapa",
        "parametros": {"ancho": 7, "largo": 10, "tipo_chapa": "galvanizada_075", "tipo_perfil": "C100"},
        "confianza": 0.88,
    }
    with patch("src.orquestador.minimax_client._cliente") as mock_cliente:
        mock_chat = AsyncMock()
        mock_chat.completions.create.return_value = _mock_completion(mock_resp)
        mock_cliente.return_value.chat = mock_chat

        foto_dummy = b"JFIF" + b"\x00" * 100  # bytes dummy
        resultado = await parsear_imagen(foto_dummy, ["CHAPA_GALVANIZADA_075"])

    assert resultado.accion == "techo_chapa"
    assert resultado.parametros["ancho"] == 7
    assert resultado.confianza == 0.88


def _mock_completion(raw: dict):
    """Helper: crea un mock de ChatCompletion con el JSON dado."""
    import json
    from unittest.mock import MagicMock
    c = MagicMock()
    c.choices[0].message.content = json.dumps(raw)
    c.usage.prompt_tokens = 500
    c.usage.completion_tokens = 80
    return c
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
- **TAREA 14:** la invalidación de caché es **automática** — editar el CSV cambia su mtime y `_mtime_signature()` devuelve un tuple diferente en la próxima llamada a `cargar_empresa()`. No hace falta llamar a ninguna función de limpieza de caché.
- **TAREA 15:** Si MiniMax-M2 rechaza el request de visión (error 400/422), implementar el fallback del PASO E que pide las medidas en texto. No bloquear al usuario.
- **Orden de handlers:** en `registrar(app)`, `filters.PHOTO` debe ir ANTES de `filters.TEXT` para que las fotos no caigan en el handler de texto.
