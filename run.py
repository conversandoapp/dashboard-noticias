#!/usr/bin/env python3
"""
Punto de entrada principal.

Uso:
    python run.py                  # Ejecuta todo (requiere ANTHROPIC_API_KEY)
    python run.py --skip-claude    # Omite llamadas a Claude (útil para pruebas)
    python run.py --date 2026-05-13
"""
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from scripts.fetch_data import recopilar
from scripts.generate_dashboard import generar_html


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Dashboard diario de noticias y mercados")
    p.add_argument("--skip-claude", action="store_true", help="No llama a la API de Claude")
    p.add_argument("--date", default=None, help="Fecha YYYY-MM-DD (por defecto: hoy)")
    return p.parse_args()


def _stub_contenido() -> dict:
    return {
        "resumen_noticias": "*(Resumen no generado — ejecuta sin --skip-claude para activar Claude)*",
        "nota_emprendimiento": "*(Nota no generada — ejecuta sin --skip-claude para activar Claude)*",
    }


def main() -> None:
    args = parse_args()

    # 1. Recopilar datos
    datos = recopilar()
    if args.date:
        datos["fecha"] = args.date

    fecha = datos["fecha"]

    # 2. Guardar datos crudos
    data_dir = ROOT / "data" / fecha
    data_dir.mkdir(parents=True, exist_ok=True)

    datos_path = data_dir / "data.json"
    datos_path.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] Datos guardados en {datos_path}")

    # 3. Generar contenido con Claude (opcional)
    if args.skip_claude:
        print("[INFO] --skip-claude activo: omitiendo Claude API")
        contenido = _stub_contenido()
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("[WARN] ANTHROPIC_API_KEY no encontrada. Usa --skip-claude o configura .env")
            contenido = _stub_contenido()
        else:
            from scripts.generate_note import generar_contenido_claude
            contenido = generar_contenido_claude(datos)

    # Guardar contenido Claude junto a los datos
    contenido_path = data_dir / "contenido_claude.json"
    contenido_path.write_text(json.dumps(contenido, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4. Generar dashboard HTML
    html_path = data_dir / "dashboard.html"
    generar_html(datos, contenido, html_path)

    # 5. Copiar como "latest"
    latest_dir = ROOT / "data" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    (latest_dir / "dashboard.html").write_bytes(html_path.read_bytes())
    (latest_dir / "data.json").write_bytes(datos_path.read_bytes())
    print(f"[INFO] Copia 'latest' actualizada en {latest_dir}")

    print(f"\n✓ Dashboard listo: {html_path}")
    print(f"  Abre en tu navegador: file://{html_path.resolve()}")


if __name__ == "__main__":
    main()
