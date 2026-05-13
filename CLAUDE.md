# Dashboard Noticias & Mercados

Repositorio que almacena el dashboard diario generado con Claude.

## Estructura

```
data/
  YYYY-MM-DD/
    data.json           # Datos crudos: noticias RSS + mercados yfinance
    contenido_claude.json  # Resumen y nota generados por Claude
    dashboard.html      # Dashboard HTML listo para abrir
  latest/
    dashboard.html      # Siempre el dashboard más reciente
    data.json
scripts/
  fetch_data.py         # Obtiene noticias (RSS) y mercados (yfinance)
  generate_note.py      # Llama a Claude API para resumen y nota de emprendimiento
  generate_dashboard.py # Genera el HTML del dashboard
run.py                  # Punto de entrada principal
```

## Requisitos

```bash
pip install -r requirements.txt
cp .env.example .env   # Luego edita .env con tu ANTHROPIC_API_KEY
```

## Uso manual

```bash
# Ejecución completa (noticias + mercados + Claude)
python run.py

# Sin llamadas a Claude (útil para probar)
python run.py --skip-claude

# Para una fecha específica
python run.py --date 2026-05-14
```

## Para Claude Code Routines

Cuando configures la rutina diaria, el comando a ejecutar es:

```bash
pip install -r requirements.txt && python run.py
```

Variables de entorno necesarias:
- `ANTHROPIC_API_KEY` — clave de la API de Anthropic

El dashboard generado se guarda en `data/YYYY-MM-DD/dashboard.html`
y se copia como `data/latest/dashboard.html`.

## Fuentes de datos

- **Noticias**: Reuters (mundo + negocios), BBC (mundo + negocios), TechCrunch, The Verge
- **Mercados**: S&P 500, Nasdaq, Dow Jones, VIX, Oro, Petróleo, Bitcoin, USD Index (vía yfinance)
- **Análisis**: Claude API (resumen de noticias + nota de emprendimiento)
