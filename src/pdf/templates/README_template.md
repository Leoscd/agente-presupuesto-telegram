# Templates PDF custom

Un arquitecto puede subir su propio template para que los presupuestos lleven la identidad del estudio.

## Estructura esperada

Subí un `.zip` por Telegram con `/template`:

```
presupuesto.html.j2   ← template Jinja2 (obligatorio)
styles.css            ← opcional; si existe, lo vincula el HTML
assets/               ← opcional: logo, fuentes, imágenes
```

El sistema los guarda en `empresas/{tu_empresa}/pdf_template/` y los usa en lugar del default.

## Variables disponibles en el template

| Variable | Tipo | Descripción |
|---|---|---|
| `empresa.nombre` | str | Nombre del estudio |
| `empresa.direccion` | str \| None | |
| `empresa.telefono` | str \| None | |
| `empresa.email` | str \| None | |
| `empresa.cuit` | str \| None | |
| `fecha` | str | ISO (YYYY-MM-DD) |
| `id_corto` | str | 6 hex chars, único por presupuesto |
| `cliente` | str | "—" si no se ingresó |
| `resultado.rubro` | str | Ej: "Techo de chapa" |
| `resultado.partidas` | list[Partida] | Ver abajo |
| `resultado.subtotal_materiales` | Decimal | |
| `resultado.subtotal_mano_obra` | Decimal | |
| `resultado.total` | Decimal | |
| `resultado.metadata` | dict | Ej: `{ancho_m, largo_m, superficie_m2, ...}` |
| `resultado.advertencias` | list[str] | |

`Partida`: `concepto`, `cantidad`, `unidad`, `precio_unitario`, `subtotal`, `categoria` (`"material"` / `"mano_obra"` / `"equipo"`).

## Filtros Jinja2 custom

- `| moneda` → formato argentino `$ 1.234.567,89`

## Reglas de seguridad

Por razones de seguridad, el uploader rechaza templates que:

- Incluyan `<script>` o handlers `on*=`
- Carguen recursos de URLs externas (`http://`, `https://`, `//`)
- Contengan directivas Jinja peligrosas (`{% import %}` con módulos no-template)

Todos los assets deben referenciarse con paths relativos dentro del zip.

## Referencia

Mirá el template default (`src/pdf/templates/default/`) como ejemplo completo.
