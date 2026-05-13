"""
Recopila noticias (RSS) y datos de mercado (yfinance).
Devuelve un dict con toda la información del día.
"""
import json
import datetime
import feedparser
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
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dow": "^DJI",
    "vix": "^VIX",
    "oro": "GC=F",
    "petroleo": "CL=F",
    "btc": "BTC-USD",
    "dxy": "DX-Y.NYB",
}


def _fetch_rss(name: str, url: str, max_items: int = 5) -> list[dict]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:max_items]:
        items.append({
            "titulo": entry.get("title", ""),
            "resumen": entry.get("summary", "")[:300],
            "url": entry.get("link", ""),
            "publicado": entry.get("published", ""),
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


def _ticker_info(symbol: str, period: str = "5d") -> dict:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)
    if hist.empty:
        return {"error": "sin datos"}

    closes = hist["Close"].tolist()
    dates = [d.strftime("%Y-%m-%d") for d in hist.index]
    ultimo = closes[-1] if closes else None
    anterior = closes[-2] if len(closes) >= 2 else ultimo
    cambio_pct = ((ultimo - anterior) / anterior * 100) if anterior else 0

    return {
        "ultimo": round(ultimo, 2) if ultimo else None,
        "cambio_pct": round(cambio_pct, 2),
        "cierre_anterior": round(anterior, 2) if anterior else None,
        "historico_fechas": dates,
        "historico_cierres": [round(c, 2) for c in closes],
    }


def _sp500_extended(period: str = "3mo") -> dict:
    ticker = yf.Ticker("^GSPC")
    hist = ticker.history(period=period)
    if hist.empty:
        return {}
    closes = hist["Close"].tolist()
    dates = [d.strftime("%Y-%m-%d") for d in hist.index]
    maximo = max(closes)
    minimo = min(closes)
    ultimo = closes[-1]
    primero = closes[0]
    rendimiento_periodo = round((ultimo - primero) / primero * 100, 2)
    return {
        "ultimo": round(ultimo, 2),
        "maximo_periodo": round(maximo, 2),
        "minimo_periodo": round(minimo, 2),
        "rendimiento_periodo_pct": rendimiento_periodo,
        "historico_fechas": dates,
        "historico_cierres": [round(c, 2) for c in closes],
    }


def fetch_mercados() -> dict:
    mercados: dict[str, dict] = {}
    for nombre, simbolo in MARKET_TICKERS.items():
        try:
            mercados[nombre] = _ticker_info(simbolo)
        except Exception as exc:
            mercados[nombre] = {"error": str(exc)}

    try:
        mercados["sp500"] = _sp500_extended()
    except Exception as exc:
        mercados["sp500"] = {"error": str(exc)}

    return mercados


def recopilar() -> dict:
    hoy = datetime.date.today().isoformat()
    print(f"[INFO] Recopilando datos para {hoy}...")

    noticias = fetch_noticias()
    print(f"[INFO] Noticias: {sum(len(v) for v in noticias.values())} artículos")

    mercados = fetch_mercados()
    print(f"[INFO] Mercados: {list(mercados.keys())}")

    return {
        "fecha": hoy,
        "generado_en": datetime.datetime.utcnow().isoformat() + "Z",
        "noticias": noticias,
        "mercados": mercados,
    }


if __name__ == "__main__":
    datos = recopilar()
    print(json.dumps(datos, indent=2, ensure_ascii=False)[:500])
