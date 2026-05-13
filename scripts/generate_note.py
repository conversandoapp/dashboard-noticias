"""
Usa la API de Claude para:
  1. Generar un resumen de las noticias más importantes del día.
  2. Escribir una nota de emprendimiento / innovación.
"""
import os
import anthropic


_CLIENT: anthropic.Anthropic | None = None


def _client() -> anthropic.Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _CLIENT


def _call(system: str, user: str, max_tokens: int = 1024) -> str:
    msg = _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


def generar_resumen_noticias(noticias: dict[str, list[dict]]) -> str:
    titulos_por_categoria = []
    for categoria, items in noticias.items():
        titulos = [f"- {n['titulo']} ({n['fuente']})" for n in items[:5]]
        if titulos:
            titulos_por_categoria.append(f"**{categoria.upper()}**\n" + "\n".join(titulos))

    corpus = "\n\n".join(titulos_por_categoria)

    system = (
        "Eres un editor ejecutivo de noticias. Redactas resúmenes concisos y directos "
        "para una persona de negocios que quiere estar informada en 2 minutos."
    )
    user = (
        f"Aquí están los titulares de hoy agrupados por categoría:\n\n{corpus}\n\n"
        "Selecciona las 5 noticias más relevantes e impactantes, y redacta un párrafo "
        "breve (2-3 oraciones) por cada una explicando por qué importa. "
        "Usa formato Markdown con un ## para cada noticia."
    )
    return _call(system, user, max_tokens=1200)


def generar_nota_emprendimiento(noticias: dict[str, list[dict]], mercados: dict) -> str:
    titulos_tech = [n["titulo"] for n in noticias.get("tecnologia", [])[:6]]
    sp500 = mercados.get("sp500", {})
    rendimiento = sp500.get("rendimiento_periodo_pct", "N/D")
    ultimo_sp = sp500.get("ultimo", "N/D")

    system = (
        "Eres un asesor de innovación y emprendimiento. Escribes reflexiones prácticas "
        "e inspiradoras que conectan las tendencias del día con oportunidades reales "
        "para emprendedores e innovadores."
    )
    user = (
        f"Contexto del día:\n"
        f"- S&P 500 en {ultimo_sp} (rendimiento trimestral: {rendimiento}%)\n"
        f"- Titulares tech de hoy: {', '.join(titulos_tech)}\n\n"
        "Escribe una nota de 200-250 palabras sobre una oportunidad de emprendimiento "
        "o innovación que surge del contexto de hoy. Sé concreto, práctico y termina "
        "con una acción que el lector puede tomar esta semana. Usa Markdown."
    )
    return _call(system, user, max_tokens=600)


def generar_contenido_claude(datos: dict) -> dict:
    print("[INFO] Generando resumen de noticias con Claude...")
    resumen = generar_resumen_noticias(datos["noticias"])

    print("[INFO] Generando nota de emprendimiento con Claude...")
    nota = generar_nota_emprendimiento(datos["noticias"], datos["mercados"])

    return {
        "resumen_noticias": resumen,
        "nota_emprendimiento": nota,
    }
