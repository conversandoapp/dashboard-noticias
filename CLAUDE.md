# Dashboard Noticias & Mercados

Repositorio que almacena el dashboard diario generado con Claude.

## Estructura

```
data/
  YYYY-MM-DD/
    data.json              # Datos crudos: noticias RSS + mercados yfinance
    contenido_claude.json  # Resumen y nota escritos por Claude (parte de la rutina)
    dashboard.html         # Dashboard HTML listo para abrir
  latest/
    dashboard.html         # Siempre el dashboard más reciente
    data.json
scripts/
  fetch_data.py            # Descarga noticias (RSS) y mercados (yfinance)
  generate_dashboard.py    # Genera el HTML a partir de data.json + contenido_claude.json
run.py                     # Orquestador: fetch + render (sin llamadas a Claude API)
```

## Requisitos

```bash
pip install -r requirements.txt
```

No se necesita `ANTHROPIC_API_KEY` en el repositorio. Claude actúa como agente
externo (vía Routines) y escribe directamente los archivos de contenido.

## Flujo de la rutina diaria

La rutina sigue estos pasos en orden:

### Paso 1 — Descargar datos
```bash
pip install -r requirements.txt
python run.py --fetch-only
```
Esto guarda `data/YYYY-MM-DD/data.json` con noticias RSS y precios de mercado.

### Paso 2 — Claude lee los datos y genera el contenido
Claude lee `data/YYYY-MM-DD/data.json` y escribe `data/YYYY-MM-DD/contenido_claude.json`
con este formato exacto:
```json
{
  "resumen_noticias": "<markdown con las 5 noticias más importantes y por qué importan>",
  "nota_emprendimiento": "<markdown con nota de 200-250 palabras sobre oportunidad de emprendimiento>"
}
```

### Paso 3 — Generar el dashboard HTML
```bash
python run.py
```
Lee `data.json` + `contenido_claude.json` y genera `dashboard.html`.

### Paso 4 — Guardar en el repositorio
```bash
git add data/
git commit -m "Dashboard YYYY-MM-DD"
git push origin HEAD:main
```

---

## Prompt para Claude Code Routines

Copia este prompt exacto al configurar la rutina:

```
Ejecuta el dashboard diario de noticias y mercados siguiendo estos pasos:

1. Instala dependencias e instala descarga datos:
   pip install -r requirements.txt && python run.py --fetch-only

2. Lee el archivo data/<FECHA>/data.json que acaba de generarse.

3. Analiza los datos y escribe el archivo data/<FECHA>/contenido_claude.json con:
   - "resumen_noticias": selecciona las 5 noticias más impactantes y escribe
     2-3 oraciones por cada una explicando por qué importa. Usa Markdown con ## por noticia.
   - "nota_emprendimiento": 200-250 palabras conectando las tendencias del día
     con una oportunidad concreta para emprendedores. Termina con una acción
     que el lector puede tomar esta semana. Usa Markdown.

4. Genera el dashboard:
   python run.py

5. Haz commit y push directo a main:
   git add data/
   git commit -m "Dashboard <FECHA>"
   git push origin HEAD:main
```

---

## Fuentes de datos

- **Noticias**: Reuters (mundo + negocios), BBC (mundo + negocios), TechCrunch, The Verge
- **Mercados**: S&P 500 (3 meses), Nasdaq, Dow Jones, VIX, Oro, Petróleo, Bitcoin, USD Index (yfinance)
- **Análisis**: Claude (como agente de la rutina, sin API key separada)
