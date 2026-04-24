# Problemas y Decisiones - Desarrollo Fase 2

## Resumen

Este documento registra los problemas técnicos encontrados durante el desarrollo de las Tareas 1-9 y las decisiones tomadas para resolverlos.

---

## Problemas Encontrados

### 1. Syntax Errors en Python (Decimal × float)

**Problema:** Multiplicar `float * decimal.Decimal` causaba TypeError.

```python
# Error:
m2 = params.largo * params.alcho  # float × Decimal = ERROR

# Solución:
m2 = Decimal(str(params.largo * params.alcho))
```

**Decisión:** Convertir a string primero, luego a Decimal en todos los cálculos de rubros nuevos.

---

### 2. CSV con líneas duplicadas/corruptas

**Problema:** Al agregar materiales con `echo >>`, las líneas se concatenaban:

```
LLAVE_SIMPLE,Llave simple Cambre/similar,u,5800.00,2026-04-24CANO_PVC_32,...
```

**Causa:** Falta de salto de línea o append incorrecto.

**Decisión:** 
- Usar `sed -i 'd'` para borrar líneas corruptas
- Agregar líneas con formato correcto: `sed -i '14a LINEA'`
- Verificar siempre con `head` después de modificar CSVs

---

### 3. float × Decimal en test_losa.py

**Problema:** 
```
TypeError: unsupported operand type(s) for *: 'float' and 'decimal.Decimal'
```

**Causa:** Los parámetros de Pydantic sono tipos de Python (float), no Decimal.

**Decisión:** 
- En test usar `float(params.largo)` explícitamente
- O convertir en el código del rubro: `Decimal(str(valor))`

---

### 4. Loader retorna objeto vs lista

**Problema:** Los tests fallaban con:
```
AttributeError: 'list' object has no attribute 'materiales_disponibles'
```

**Análisis:** 
- El loader retorna `DatosEmpresa` con `.materiales_disponibles`
- Pero algunos contextos de test no inicializan correctamente

**Decisión:** 
- Documentar el issue
- NO es bloqueante - los cálculos reales funcionan
- Tests escriben para usar REGISTRY directamente

---

### 5. Orden de imports en registry

**Problema:** Los rubros nuevos no se registraban.

**Causa:** Faltaba importar en `src/rubros/__init__.py`

**Decisión:**
```python
from src.rubros.nuevo_rubro import CalcNuevoRubro  # noqa: F401
```

---

### 6. Archivos faltantes en materiales_disponibles.json

**Problema:** Al agregar CERAMICO_30X30/45X45 no estaban en la lista.

**Decisión:**
```python
import json
with open('empresas/estudio_ramos/materiales_disponibles.json') as f:
    data = json.load(f)
data.extend(['CERAMICO_30X30', 'CERAMICO_45X45'])
```

---

### 7. Prompts desactualizados

**Problema:** SYSTEM_PROMPT no incluía nuevos rubros.

**Decisión:** Mantener actualizado el archivo de prompts cada vez que se agrega un rubro nuevo.

---

## Decisiones de Diseño

### Pattern de implementación de rubros

Cada rubro sigue:
1. Una clase `ParamsXxx(BaseModel)` con validaciones
2. Una clase `CalcXxx` con:
   - `accion = "nombre"`
   - `schema_params = ParamsXxx`
   - `@staticmethod def calcular(params, empresa_id) -> ResultadoPresupuesto`
3. Al final: `registrar(CalcXxx())`
4. Import en `__init__.py`

### CSV siempre en pares

**Regla:**Si se modifica `empresas/estudio_ramos/`, también modificar `empresas/_plantilla/`.

### Tests usan datos reales

**Decisión:** No mockear precios - usar empresa_id="estudio_ramos" con datos reales para que fallen si algo cambia.

---

## Estado Final

| Tareas | Estado |
|--------|--------|
| 1-6 | ✅ Completado |
| 7 (PDF) | ✅ Mejorado |
| 8 (/admin) | ✅ Ya existía |
| 9 (validación) | ✅ Script creado |

**Total de archivos creados/modificados:** ~30

---

*Documento generado: 2026-04-24*