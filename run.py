#!/usr/bin/env python3
"""
Punto de entrada principal — solo obtiene datos y genera el HTML.
La generación de texto (resumen, nota) la realiza Claude directamente
como parte de la rutina, escribiendo contenido_claude.json.

Uso:
    python run.py                  # fetch + genera HTML (requiere contenido_claude.json previo)
    python run.py --date 2026-05-14
    python run.py --fetch-only     # Solo descarga datos, sin generar HTML
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from scripts.fetch_data import fetch_noticias, fetch_mercados
from scripts.generate_dashboard import generar_html

import datetime


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=None)
    p.add_argument("--fetch-only", action="store_true", help="Solo descarga datos")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    fecha = args.date or datetime.date.today().isoformat()

    # 1. Recopilar datos
    print(f"[INFO] Recopilando datos para {fecha}...")
    noticias = fetch_noticias()
    mercados = fetch_mercados()

    datos = {
        "fecha": fecha,
        "generado_en": datetime.datetime.utcnow().isoformat() + "Z",
        "noticias": noticias,
        "mercados": mercados,
    }

    # 2. Guardar data.json
    data_dir = ROOT / "data" / fecha
    data_dir.mkdir(parents=True, exist_ok=True)
    datos_path = data_dir / "data.json"
    datos_path.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] Datos guardados en {datos_path}")

    if args.fetch_only:
        print("[INFO] --fetch-only: terminando aquí.")
        print(f"  Siguiente paso: Claude lee {datos_path} y escribe contenido_claude.json")
        return

    # 3. Leer contenido generado por Claude
    contenido_path = data_dir / "contenido_claude.json"
    if not contenido_path.exists():
        print(f"[WARN] {contenido_path} no existe — genera el contenido con Claude primero.")
        print("       En modo manual puedes crear ese archivo con el formato:")
        print('       {"resumen_noticias": "...", "nota_emprendimiento": "..."}')
        return

    contenido = json.loads(contenido_path.read_text(encoding="utf-8"))

    # 4. Generar dashboard HTML
    html_path = data_dir / "dashboard.html"
    generar_html(datos, contenido, html_path)

    # 5. Actualizar latest/
    latest_dir = ROOT / "data" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    (latest_dir / "dashboard.html").write_bytes(html_path.read_bytes())
    (latest_dir / "data.json").write_bytes(datos_path.read_bytes())
    print(f"[INFO] latest/ actualizado")

    print(f"\n✓ Dashboard listo: {html_path}")


if __name__ == "__main__":
    main()
