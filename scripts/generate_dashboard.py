"""
Genera el dashboard HTML a partir de los datos recopilados y el contenido de Claude.
"""
import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Markdown → HTML mínimo (sin dependencias externas)
# ---------------------------------------------------------------------------

def _md_to_html(text: str) -> str:
    """Convierte Markdown básico a HTML."""
    lines = text.split("\n")
    html_lines = []
    in_ul = False

    for line in lines:
        # Encabezados
        if line.startswith("### "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<h1>{line[2:]}</h1>")
        # Listas
        elif line.startswith("- ") or line.startswith("* "):
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{line[2:]}</li>")
        # Línea vacía
        elif line.strip() == "":
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append("<br>")
        else:
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            html_lines.append(f"<p>{line}</p>")

    if in_ul:
        html_lines.append("</ul>")

    result = "\n".join(html_lines)
    # Inline: **bold**, *italic*
    result = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", result)
    result = re.sub(r"\*(.+?)\*", r"<em>\1</em>", result)
    return result


# ---------------------------------------------------------------------------
# Helpers para métricas de mercado
# ---------------------------------------------------------------------------

def _arrow(pct: float) -> str:
    return "▲" if pct >= 0 else "▼"


def _color_class(pct: float) -> str:
    return "up" if pct >= 0 else "down"


def _fmt_pct(pct) -> str:
    if pct is None:
        return "N/D"
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _market_card(label: str, datos: dict, prefix: str = "") -> str:
    if "error" in datos:
        return f'<div class="market-card"><span class="market-label">{label}</span><span class="market-value">—</span></div>'
    val = datos.get("ultimo", "—")
    pct = datos.get("cambio_pct", 0)
    arrow = _arrow(pct)
    cls = _color_class(pct)
    return (
        f'<div class="market-card">'
        f'<span class="market-label">{label}</span>'
        f'<span class="market-value">{prefix}{val:,.2f}</span>'
        f'<span class="market-change {cls}">{arrow} {_fmt_pct(pct)}</span>'
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Construcción del HTML
# ---------------------------------------------------------------------------

_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard · {fecha}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #222636;
    --border: #2d3148;
    --text: #e2e8f0;
    --text2: #94a3b8;
    --accent: #6366f1;
    --up: #10b981;
    --down: #ef4444;
    --gold: #f59e0b;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; }}

  /* Header */
  .header {{ background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 2rem; border-bottom: 1px solid var(--border); }}
  .header-inner {{ max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; }}
  .header h1 {{ font-size: 1.6rem; font-weight: 700; letter-spacing: -0.5px; }}
  .header h1 span {{ color: #a5b4fc; }}
  .header .fecha {{ color: #a5b4fc; font-size: 0.9rem; }}

  /* Layout */
  .main {{ max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; display: grid; gap: 1.5rem; }}

  /* Section title */
  .section-title {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--accent); margin-bottom: 1rem; }}

  /* Market strip */
  .markets-strip {{ display: flex; flex-wrap: wrap; gap: 0.75rem; }}
  .market-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1rem 1.25rem; min-width: 140px; flex: 1; display: flex; flex-direction: column; gap: 0.25rem; }}
  .market-label {{ font-size: 0.75rem; color: var(--text2); text-transform: uppercase; letter-spacing: 0.5px; }}
  .market-value {{ font-size: 1.25rem; font-weight: 700; }}
  .market-change {{ font-size: 0.85rem; font-weight: 600; }}
  .market-change.up {{ color: var(--up); }}
  .market-change.down {{ color: var(--down); }}

  /* Chart card */
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.5rem; }}
  .chart-wrap {{ position: relative; height: 240px; }}

  /* Grid 2 cols */
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

  /* News */
  .news-list {{ display: flex; flex-direction: column; gap: 0.75rem; }}
  .news-item {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 0.5rem; padding: 0.9rem 1rem; }}
  .news-item .fuente {{ font-size: 0.7rem; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; }}
  .news-item .titulo {{ font-size: 0.9rem; font-weight: 600; line-height: 1.4; }}
  .news-item a {{ color: var(--text); text-decoration: none; }}
  .news-item a:hover {{ color: #a5b4fc; }}
  .news-item .resumen {{ font-size: 0.8rem; color: var(--text2); margin-top: 0.3rem; }}

  /* Claude content */
  .claude-content h1,
  .claude-content h2 {{ font-size: 1rem; font-weight: 700; color: #a5b4fc; margin: 1rem 0 0.4rem; }}
  .claude-content h3 {{ font-size: 0.95rem; font-weight: 600; margin: 0.8rem 0 0.3rem; }}
  .claude-content p {{ font-size: 0.88rem; color: var(--text2); margin-bottom: 0.5rem; }}
  .claude-content ul {{ padding-left: 1.2rem; }}
  .claude-content li {{ font-size: 0.88rem; color: var(--text2); margin-bottom: 0.3rem; }}
  .claude-content strong {{ color: var(--text); }}

  /* Note card */
  .note-card {{ background: linear-gradient(135deg, #1e1b4b22 0%, #31298133 100%); border: 1px solid #6366f144; border-radius: 0.75rem; padding: 1.5rem; }}

  /* Footer */
  .footer {{ text-align: center; padding: 2rem; color: var(--text2); font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 2rem; }}

  /* Tabs */
  .tabs {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; }}
  .tab {{ padding: 0.4rem 1rem; border-radius: 999px; border: 1px solid var(--border); background: transparent; color: var(--text2); cursor: pointer; font-size: 0.8rem; transition: all 0.2s; }}
  .tab.active {{ background: var(--accent); border-color: var(--accent); color: white; }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}
</style>
</head>
<body>

<header class="header">
  <div class="header-inner">
    <h1>Dashboard <span>Noticias & Mercados</span></h1>
    <div class="fecha">{fecha_larga} · Generado con Claude</div>
  </div>
</header>

<main class="main">

  <!-- MERCADOS STRIP -->
  <section>
    <div class="section-title">Mercados al cierre</div>
    <div class="markets-strip">
      {market_cards}
    </div>
  </section>

  <!-- S&P 500 CHART -->
  <section class="card">
    <div class="section-title">S&P 500 — últimos 3 meses</div>
    <div class="chart-wrap">
      <canvas id="spChart"></canvas>
    </div>
  </section>

  <!-- NOTICIAS + RESUMEN -->
  <div class="grid-2">

    <section class="card">
      <div class="section-title">Titulares del día</div>
      <div class="tabs">
        <button class="tab active" onclick="showTab(event,'tab-mundo')">Mundo</button>
        <button class="tab" onclick="showTab(event,'tab-negocios')">Negocios</button>
        <button class="tab" onclick="showTab(event,'tab-tecnologia')">Tecnología</button>
      </div>
      <div id="tab-mundo" class="tab-panel active">
        <div class="news-list">{noticias_mundo}</div>
      </div>
      <div id="tab-negocios" class="tab-panel">
        <div class="news-list">{noticias_negocios}</div>
      </div>
      <div id="tab-tecnologia" class="tab-panel">
        <div class="news-list">{noticias_tecnologia}</div>
      </div>
    </section>

    <section class="card">
      <div class="section-title">Resumen inteligente · Claude</div>
      <div class="claude-content">{resumen_html}</div>
    </section>

  </div>

  <!-- NOTA EMPRENDIMIENTO -->
  <section class="note-card">
    <div class="section-title">Nota de emprendimiento e innovación</div>
    <div class="claude-content">{nota_html}</div>
  </section>

</main>

<footer class="footer">
  Dashboard generado el {generado_en} · datos: Reuters, BBC, yfinance · análisis: Claude API
</footer>

<script>
// S&P 500 chart
const spLabels = {sp_labels};
const spData   = {sp_data};

const spCtx = document.getElementById('spChart').getContext('2d');
new Chart(spCtx, {{
  type: 'line',
  data: {{
    labels: spLabels,
    datasets: [{{
      label: 'S&P 500',
      data: spData,
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99,102,241,0.08)',
      borderWidth: 2,
      pointRadius: 0,
      fill: true,
      tension: 0.3,
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{
        ticks: {{ color: '#64748b', maxTicksLimit: 6 }},
        grid: {{ color: '#1e2235' }},
      }},
      y: {{
        ticks: {{ color: '#64748b', callback: v => v.toLocaleString() }},
        grid: {{ color: '#1e2235' }},
      }}
    }}
  }}
}});

// Tabs
function showTab(e, id) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  e.target.classList.add('active');
}}
</script>
</body>
</html>
"""


def _noticias_html(items: list[dict]) -> str:
    if not items:
        return "<p style='color:#64748b'>Sin noticias disponibles</p>"
    partes = []
    for n in items[:8]:
        titulo = n.get("titulo", "")
        url = n.get("url", "#")
        fuente = n.get("fuente", "")
        resumen = n.get("resumen", "")[:200]
        partes.append(
            f'<div class="news-item">'
            f'<div class="fuente">{fuente}</div>'
            f'<div class="titulo"><a href="{url}" target="_blank" rel="noopener">{titulo}</a></div>'
            f'<div class="resumen">{resumen}</div>'
            f"</div>"
        )
    return "\n".join(partes)


def generar_html(datos: dict, contenido_claude: dict, output_path: Path) -> Path:
    mercados = datos.get("mercados", {})
    noticias = datos.get("noticias", {})
    fecha = datos.get("fecha", "")
    generado_en = datos.get("generado_en", "")

    # Fecha larga
    import datetime
    try:
        dt = datetime.date.fromisoformat(fecha)
        meses = ["enero","febrero","marzo","abril","mayo","junio",
                 "julio","agosto","septiembre","octubre","noviembre","diciembre"]
        dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
        fecha_larga = f"{dias[dt.weekday()].capitalize()} {dt.day} de {meses[dt.month-1]} de {dt.year}"
    except Exception:
        fecha_larga = fecha

    # Market cards
    cards_config = [
        ("S&P 500", "sp500", ""),
        ("Nasdaq", "nasdaq", ""),
        ("Dow Jones", "dow", ""),
        ("VIX", "vix", ""),
        ("Oro", "oro", "$"),
        ("Petróleo", "petroleo", "$"),
        ("Bitcoin", "btc", "$"),
        ("USD Index", "dxy", ""),
    ]
    market_cards_html = "\n".join(
        _market_card(label, mercados.get(key, {}), prefix)
        for label, key, prefix in cards_config
    )

    # S&P data for chart
    sp = mercados.get("sp500", {})
    sp_labels = json.dumps(sp.get("historico_fechas", []))
    sp_data = json.dumps(sp.get("historico_cierres", []))

    html = _TEMPLATE.format(
        fecha=fecha,
        fecha_larga=fecha_larga,
        generado_en=generado_en,
        market_cards=market_cards_html,
        sp_labels=sp_labels,
        sp_data=sp_data,
        noticias_mundo=_noticias_html(noticias.get("mundo", [])),
        noticias_negocios=_noticias_html(noticias.get("negocios", [])),
        noticias_tecnologia=_noticias_html(noticias.get("tecnologia", [])),
        resumen_html=_md_to_html(contenido_claude.get("resumen_noticias", "")),
        nota_html=_md_to_html(contenido_claude.get("nota_emprendimiento", "")),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"[INFO] Dashboard guardado en {output_path}")
    return output_path
