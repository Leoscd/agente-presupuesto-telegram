# Agente de Presupuestos — Telegram + MiniMax-M2

Bot de Telegram que recibe pedidos en lenguaje natural ("techo chapa 7x10 con perfil C100") y devuelve presupuestos precisos + PDF formal con la marca del estudio.

**Arquitectura:** MiniMax-M2 **solo orquesta** (NLU → JSON). Todo el cálculo, validación y precios corren en Python determinístico.

## Requisitos

- Python 3.11+
- WeasyPrint dependencias nativas (en Windows se instalan solas con el pip wheel; en Linux: `apt install libpango-1.0-0 libpangoft2-1.0-0`)

## Setup dev

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -e ".[dev]"
cp .env.example .env          # completa TELEGRAM_TOKEN y MINIMAX_API_KEY
python -m src.bot.main        # arranca bot en modo polling
```

## Tests

```bash
pytest                                  # unit + property tests
python -m scripts.correr_golden         # regresión contra presupuestos reales
```

## Agregar una empresa

```bash
python -m scripts.nueva_empresa "Estudio Ramos"
# edita empresas/estudio_ramos/precios_materiales.csv y demás
```

## Documentación

- `C:\Users\leona\.claude\plans\en-esta-carpeta-tengo-keen-cray.md` — plan completo
- `src/pdf/templates/README_template.md` — cómo crear un template PDF custom
