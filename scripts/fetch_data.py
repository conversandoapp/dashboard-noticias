"""
Recopila noticias (RSS) y datos de mercado (yfinance) y los guarda en data/<fecha>/data.json.

Uso:
    python scripts/fetch_data.py
    python scripts/fetch_data.py --date 2026-05-14
"""
import argparse
import datetime
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
import yfinance as yf


RSS_FEEDS = {
    "mundo": [
        ("Reuters - Top News", "https://feeds.reuters.com/reuters/topNews"),
        ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
    ],
    "negocios": [
        ("Reuters - Business", "https://feeds.reuters.com/reuters/businessNews"),
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ],
    "tecnologia": [
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ],
}

MARKET_TICKERS = {
    "nasdaq": "^IXIC",
    "dow": "^DJI",
    "vix": "^VIX",
    "oro": "GC=F",
    "petroleo": "CL=F",
    "btc": "BTC-USD",
    "dxy": "DX-Y.NYB",
}


def _fetch_rss(name: str, url: str, max_items: int = 6) -> list[dict]:
    NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "media": "http://search.yahoo.com/mrss/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as exc:
        print(f"[WARN] No se pudo parsear {name}: {exc}")
        return []

    items = []
    # RSS 2.0
    for item in root.findall(".//item")[:max_items]:
        titulo = item.findtext("title") or ""
        resumen = item.findtext("description") or ""
        link = item.findtext("link") or ""
        publicado = item.findtext("pubDate") or item.findtext("dc:date", namespaces=NS) or ""
        items.append({
            "titulo": titulo.strip(),
            "resumen": resumen.strip()[:400],
            "url": link.strip(),
            "publicado": publicado.strip(),
            "fuente": name,
        })
    # Atom
    if not items:
        for entry in root.findall(".//atom:entry", NS)[:max_items]:
            titulo = entry.findtext("atom:title", namespaces=NS) or ""
            resumen = entry.findtext("atom:summary", namespaces=NS) or entry.findtext("atom:content", namespaces=NS) or ""
            link_el = entry.find("atom:link", NS)
            link = link_el.get("href", "") if link_el is not None else ""
            publicado = entry.findtext("atom:published", namespaces=NS) or entry.findtext("atom:updated", namespaces=NS) or ""
            items.append({
                "titulo": titulo.strip(),
                "resumen": resumen.strip()[:400],
                "url": link.strip(),
                "publicado": publicado.strip(),
                "fuente": name,
            })
    return items


def fetch_noticias() -> dict[str, list[dict]]:
    resultado: dict[str, list[dict]] = {}
    for categoria, fuentes in RSS_FEEDS.items():
        noticias: list[dict] = []
        for nombre, url in fuentes:
            try:
                noticias.extend(_fetch_rss(nombre, url))
            except Exception as exc:
                print(f"[WARN] RSS {nombre}: {exc}")
        resultado[categoria] = noticias
    return resultado


def _ticker_snapshot(symbol: str, period: str = "5d") -> dict:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)
    if hist.empty:
        return {"error": "sin datos"}
    closes = hist["Close"].tolist()
    dates = [d.strftime("%Y-%m-%d") for d in hist.index]
    ultimo = closes[-1]
    anterior = closes[-2] if len(closes) >= 2 else ultimo
    cambio_pct = (ultimo - anterior) / anterior * 100 if anterior else 0
    return {
        "ultimo": round(ultimo, 2),
        "cambio_pct": round(cambio_pct, 2),
        "cierre_anterior": round(anterior, 2),
        "historico_fechas": dates,
        "historico_cierres": [round(c, 2) for c in closes],
    }


def _sp500_3m() -> dict:
    hist = yf.Ticker("^GSPC").history(period="3mo")
    if hist.empty:
        return {"error": "sin datos"}
    closes = hist["Close"].tolist()
    dates = [d.strftime("%Y-%m-%d") for d in hist.index]
    ultimo, primero = closes[-1], closes[0]
    anterior = closes[-2] if len(closes) >= 2 else ultimo
    return {
        "ultimo": round(ultimo, 2),
        "cambio_pct": round((ultimo - anterior) / anterior * 100, 2),
        "cierre_anterior": round(anterior, 2),
        "maximo_periodo": round(max(closes), 2),
        "minimo_periodo": round(min(closes), 2),
        "rendimiento_periodo_pct": round((ultimo - primero) / primero * 100, 2),
        "historico_fechas": dates,
        "historico_cierres": [round(c, 2) for c in closes],
    }


def fetch_mercados() -> dict:
    mercados: dict[str, dict] = {"sp500": {}}
    try:
        mercados["sp500"] = _sp500_3m()
    except Exception as exc:
        mercados["sp500"] = {"error": str(exc)}

    for nombre, simbolo in MARKET_TICKERS.items():
        try:
            mercados[nombre] = _ticker_snapshot(simbolo)
        except Exception as exc:
            mercados[nombre] = {"error": str(exc)}
    return mercados


def main() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    args = parser.parse_args()

    fecha = args.date or datetime.date.today().isoformat()
    print(f"[INFO] Recopilando datos para {fecha}...")

    noticias = fetch_noticias()
    total = sum(len(v) for v in noticias.values())
    print(f"[INFO] Noticias obtenidas: {total}")

    mercados = fetch_mercados()
    print(f"[INFO] Mercados obtenidos: {list(mercados.keys())}")

    payload = {
        "fecha": fecha,
        "generado_en": datetime.datetime.utcnow().isoformat() + "Z",
        "noticias": noticias,
        "mercados": mercados,
    }

    out = Path(__file__).parent.parent / "data" / fecha / "data.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] Guardado en {out}")
    return out


if __name__ == "__main__":
    main()
