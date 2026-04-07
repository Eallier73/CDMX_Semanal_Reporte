#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   🔗 GENERADOR DE URLs DE FACEBOOK                                       ║
║                                                                           ║
║   Descarga posts de páginas Facebook usando Apify, pero retiene          ║
║   SOLO URLs + metadata (sin guardar el contenido de los posts).          ║
║                                                                           ║
║   Las URLs generadas se alimentan a:                                      ║
║   - 4_extractors_facebook_comentarios.py (para bajar comentarios)        ║
║   - 5_extractors_facebook_posts.py (modo alternativo con CSV)            ║
║                                                                           ║
║   Uso:                                                                   ║
║   python 2_extractors_facebook_urls.py \\                                ║
║     --pages TampicoGob monicavtampico \\                                 ║
║     --since 2026-03-01 --before 2026-03-12 \\                            ║
║     --output-dir ./Facebook \\                                            ║
║     --max-urls 500                                                       ║
║                                                                           ║
║   Output: YYYY-MM-DD_Facebook/YYYY-MM-DD_urls.csv                       ║
║   Columnas: post_url, page_url, page_handle, fecha_post, fecha_post_date║
║                                                                           ║
║   Requisitos: pip install apify-client pandas                            ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import pandas as pd

from output_naming import build_report_tag


ACTOR_POSTS = "scraper_one/facebook-posts-scraper"
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_BASE_DIR = str(REPO_ROOT / "Facebook")
DEFAULT_PAGES = ["monicavtampico", "TampicoGob"]
DEFAULT_RESULTS_LIMIT_PER_PAGE = 100
DEFAULT_BATCH_SIZE = 10


# ============================================================================
# UTILIDADES
# ============================================================================

def valid_date(value: str) -> str:
    """Valida que sea una fecha YYYY-MM-DD."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Fecha invalida '{value}', usa YYYY-MM-DD") from exc
    return value


def valid_sampling_percent(value: str) -> float:
    """Valida porcentaje de sampling."""
    try:
        pct = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Sampling invalido '{value}', usa un numero entre 0 y 100."
        ) from exc

    if pct <= 0 or pct > 100:
        raise argparse.ArgumentTypeError(
            f"Sampling invalido '{value}', debe ser > 0 y <= 100."
        )
    return pct


def parse_pages_text(raw: str) -> list[str]:
    """Parsea lista de páginas separadas por espacio o coma."""
    normalizado = raw.replace(",", " ").strip()
    return [p for p in normalizado.split() if p]


def normalize_target(target: str) -> str:
    """Normaliza handle de página."""
    value = (target or "").strip()
    if not value:
        return ""

    if "facebook.com" in value.lower():
        parsed = urlparse(value)
        path = (parsed.path or "").strip("/")
        if path:
            return path.split("/")[0].lower()
        return ""

    value = value.removeprefix("@").strip("/")
    return value.lower()


def target_to_page_url(target: str) -> str:
    """Convierte handle a URL completa de Facebook."""
    value = (target or "").strip()
    if not value:
        return ""
    if value.lower().startswith("http://") or value.lower().startswith("https://"):
        return value
    value = value.removeprefix("@")
    return f"https://www.facebook.com/{value}"


def extract_handle_from_url(url: str) -> str:
    """Extrae handle desde URL de Facebook."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        path = (parsed.path or "").strip("/")
        if not path:
            return ""
        return path.split("/")[0].lower()
    except Exception:
        return ""


def parse_item_datetime(item: dict) -> Optional[datetime]:
    """Extrae datetime de un item del actor."""
    # Intentar campos de timestamp numérico
    timestamp_candidates = [
        item.get("timestamp"),
        item.get("postTimestamp"),
        item.get("createdTime"),
        item.get("createdAt"),
    ]
    for raw in timestamp_candidates:
        if raw is None:
            continue
        try:
            if isinstance(raw, str) and raw.strip().isdigit():
                raw = int(raw.strip())
            if isinstance(raw, (int, float)):
                ts = float(raw)
                if ts > 10_000_000_000:  # milisegundos
                    ts = ts / 1000.0
                return datetime.fromtimestamp(ts)
        except Exception:
            continue

    # Intentar campos de fecha string ISO
    date_candidates = [
        item.get("date"),
        item.get("postDate"),
        item.get("publishedAt"),
        item.get("createdAt"),
    ]
    for raw in date_candidates:
        text = str(raw or "").strip()
        if not text:
            continue
        try:
            if text.endswith("Z"):
                text = text.replace("Z", "+00:00")
            return datetime.fromisoformat(text).replace(tzinfo=None)
        except Exception:
            pass
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt)
            except Exception:
                continue
    return None


def in_date_range(value: Optional[datetime], since: Optional[str], before: Optional[str]) -> bool:
    """Verifica si una fecha está en rango."""
    if value is None:
        return False
    since_dt = datetime.strptime(since, "%Y-%m-%d") if since else None
    before_dt = datetime.strptime(before, "%Y-%m-%d") if before else None

    date_only = value.date()
    if since_dt and date_only < since_dt.date():
        return False
    if before_dt and date_only > before_dt.date():
        return False
    return True


def belongs_to_targets(item: dict, target_handles: set[str]) -> bool:
    """Verifica si un item pertenece a páginas target."""
    if not target_handles:
        return True

    page_url = str(item.get("page_url") or "")
    post_url = str(item.get("post_url") or "")
    explicit = str(item.get("page_handle") or "").lower().strip()
    if explicit and explicit in target_handles:
        return True

    candidates = {
        extract_handle_from_url(page_url),
        extract_handle_from_url(post_url),
    }
    if any(c and c in target_handles for c in candidates):
        return True

    page_url_l = page_url.lower()
    post_url_l = post_url.lower()
    for h in target_handles:
        token = f"/{h}/"
        if token in page_url_l or token in post_url_l:
            return True
    return False


def normalize_url_item(item: dict) -> dict:
    """Extrae SOLO metadatos de URL de un item del actor."""
    author = item.get("author") if isinstance(item.get("author"), dict) else {}

    post_url = str(
        item.get("url")
        or item.get("postUrl")
        or item.get("postURL")
        or item.get("facebookUrl")
        or ""
    ).strip()
    page_url = str(
        item.get("pageUrl")
        or item.get("authorProfileUrl")
        or author.get("url")
        or ""
    ).strip()

    dt = parse_item_datetime(item)
    dt_iso = dt.isoformat(sep=" ") if dt else ""

    return {
        "post_url": post_url,
        "page_url": page_url,
        "page_handle": extract_handle_from_url(page_url) or extract_handle_from_url(post_url),
        "fecha_post": dt_iso,
        "fecha_post_date": dt.date().isoformat() if dt else "",
    }


def run_urls_batch(client, page_urls: list[str], results_limit: int) -> list[dict]:
    """Ejecuta actor FB para un batch de páginas, retorna items crudos."""
    run_input = {
        "pageUrls": page_urls,
        "resultsLimit": results_limit,
    }

    try:
        run = client.actor(ACTOR_POSTS).call(run_input=run_input)
    except Exception as exc:
        print(f"     ❌ Error al correr actor: {exc}")
        return []

    if not run:
        print("     ❌ El actor no retornó resultado.")
        return []

    status = run.get("status", "UNKNOWN")
    cost = run.get("usageTotalUsd", 0)
    print(f"     Status: {status} | Costo: ${cost:.4f} USD")

    dataset_id = run.get("defaultDatasetId")
    if not dataset_id:
        print("     ❌ Sin dataset en respuesta del actor.")
        return []

    items = list(client.dataset(dataset_id).iterate_items())
    print(f"     ✅ {len(items)} items descargados")
    return items


def _input_con_default(label: str, default: str) -> str:
    val = input(f"{label} [{default}]: ").strip()
    return val or default


def _input_int(label: str, default: Optional[int], minimo: int = 1) -> Optional[int]:
    suffix = f" [{default}]" if default is not None else " [vacio]"
    while True:
        raw = input(f"{label}{suffix}: ").strip()
        if not raw:
            return default
        try:
            n = int(raw)
            if n < minimo:
                print(f"   Debe ser >= {minimo}")
                continue
            return n
        except ValueError:
            print("   Ingresa un entero valido.")


def _input_float(
    label: str,
    default: Optional[float],
    minimo: float = 0.01,
    maximo: float = 100.0,
) -> Optional[float]:
    suffix = f" [{default}]" if default is not None else " [vacío]"
    while True:
        raw = input(f"{label}{suffix}: ").strip()
        if not raw:
            return default
        try:
            n = float(raw)
            if n < minimo or n > maximo:
                print(f"   ⚠️ Debe estar entre {minimo} y {maximo}.")
                continue
            return n
        except ValueError:
            print("   ⚠️ Ingresa un número válido.")


def _input_date(label: str, default: str) -> str:
    while True:
        value = _input_con_default(label, default)
        try:
            valid_date(value)
            return value
        except argparse.ArgumentTypeError:
            print("   ⚠️ Formato inválido. Usa YYYY-MM-DD.")


def ejecutar_prompt_interactivo(args: argparse.Namespace) -> argparse.Namespace:
    """Ejecuta preguntas interactivas en consola."""
    print("\n" + "=" * 70)
    print("🔗 GENERADOR DE URLs FACEBOOK")
    print("=" * 70)
    print("Descarga URLs de posts de páginas Facebook.\n")

    default_pages = " ".join(args.pages or DEFAULT_PAGES)
    pages_raw = _input_con_default("Páginas (separadas por espacio o coma)", default_pages)
    args.pages = parse_pages_text(pages_raw)

    today = datetime.now().date()
    since_default = args.since or (today - timedelta(days=7)).strftime("%Y-%m-%d")
    before_default = args.before or today.strftime("%Y-%m-%d")

    args.since = _input_date("Fecha desde (YYYY-MM-DD)", since_default)
    args.before = _input_date("Fecha hasta (YYYY-MM-DD)", before_default)

    args.max_urls = _input_int("Máx URLs por página", args.max_urls, minimo=1) or 100
    args.sample_percent = _input_float(
        "Sampling URLs Facebook (%) (vacío = sin sampling)",
        args.sample_percent,
        minimo=0.01,
        maximo=100.0,
    )
    if args.sample_percent is not None:
        args.sample_seed = _input_int("Semilla sampling", args.sample_seed, minimo=0) or 42
    args.batch_size = _input_int("Batch size", args.batch_size, minimo=1) or 10

    output_raw = input(
        f"Directorio base salida [{args.output_dir}]: "
    ).strip()
    if output_raw:
        args.output_dir = output_raw

    if not (args.token or os.environ.get("APIFY_TOKEN")):
        token_raw = input("APIFY token (ENTER si ya está en APIFY_TOKEN): ").strip()
        if token_raw:
            args.token = token_raw

    return args


def parse_args():
    """Parsea argumentos de CLI."""
    parser = argparse.ArgumentParser(
        description="Genera CSV de URLs de posts de Facebook vía Apify",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:

  1) Descargar URLs de dos páginas en rango semanal:
     python 2_extractors_facebook_urls.py \\
       --pages TampicoGob monicavtampico \\
       --since 2026-03-01 --before 2026-03-12 \\
       --output-dir ./Facebook \\
       --max-urls 200

  2) Modo interactivo:
     python 2_extractors_facebook_urls.py --prompt

  3) Con sampling (si hay muchas URLs):
     python 2_extractors_facebook_urls.py \\
       --pages TampicoGob monicavtampico \\
       --since 2026-03-01 --before 2026-03-12 \\
       --output-dir ./Facebook \\
       --max-urls 500 \\
       --sample-percent 50 \\
       --sample-seed 42
        """,
    )

    parser.add_argument("--pages", nargs="+", default=None,
                        help="Handles de páginas Facebook (default: monicavtampico TampicoGob)")
    parser.add_argument("--max-urls", type=int, default=100,
                        help="Máximo de URLs descargadas por página (default: 100)")
    parser.add_argument("--sample-percent", type=valid_sampling_percent, default=None,
                        help="Sampling aleatorio de URLs en porcentaje (0-100)")
    parser.add_argument("--sample-seed", type=int, default=42,
                        help="Semilla para muestreo aleatorio (default: 42)")
    parser.add_argument("--since", required=True, type=valid_date,
                        help="Fecha inicio YYYY-MM-DD (heredada del orquestador)")
    parser.add_argument("--before", required=True, type=valid_date,
                        help="Fecha fin YYYY-MM-DD (heredada del orquestador)")
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Páginas por batch (default: 10)")
    parser.add_argument("--token", default=None,
                        help="Apify API token (o variable APIFY_TOKEN)")
    parser.add_argument("--output-dir", required=True,
                        help="Directorio base de salida (heredado del orquestador)")
    parser.add_argument("--prompt", action="store_true",
                        help="Fuerza modo interactivo (preguntas en consola)")
    parser.add_argument("--no-prompt", action="store_true",
                        help="Desactiva preguntas interactivas y usa solo CLI")

    return parser.parse_args()


def main():
    """Ejecución principal."""
    args = parse_args()
    usar_prompt = args.prompt or not args.no_prompt
    if usar_prompt:
        args = ejecutar_prompt_interactivo(args)

    # Validar fechas
    since_dt = datetime.strptime(args.since, "%Y-%m-%d")
    before_dt = datetime.strptime(args.before, "%Y-%m-%d")
    if since_dt > before_dt:
        print("❌ Fecha invalida: --since no puede ser mayor a --before.")
        sys.exit(1)

    # Validar token
    token = args.token or os.environ.get("APIFY_TOKEN")
    if not token:
        print("❌ Necesitas APIFY_TOKEN o --token para ejecutar el actor.")
        print("   Token: https://console.apify.com/settings/integrations")
        sys.exit(1)

    try:
        from apify_client import ApifyClient
    except ImportError:
        print("❌ Falta dependencia: apify-client")
        print("   Instala con: pip install apify-client pandas")
        sys.exit(1)

    # Normalizar páginas
    target_handles = [normalize_target(p) for p in args.pages]
    target_handles = [h for h in target_handles if h]
    if not target_handles:
        print("❌ No se pudieron normalizar páginas target.")
        sys.exit(1)

    page_urls = [target_to_page_url(p) for p in args.pages if str(p).strip()]
    page_urls = [u for u in page_urls if u]

    # Aplicar sampling si es necesario
    if args.sample_percent is not None and args.sample_percent < 100:
        original_count = len(page_urls)
        sample_size = max(1, round(original_count * (args.sample_percent / 100.0)))
        if sample_size < original_count:
            random.seed(args.sample_seed)
            page_urls = random.sample(page_urls, sample_size)
            print(f"🎲 Sampling páginas: {args.sample_percent:.2f}% ({sample_size}/{original_count})")

    if not page_urls:
        print("❌ No hay páginas target para procesar.")
        sys.exit(1)

    client = ApifyClient(token)

    # Header de ejecución
    print("\n" + "=" * 70)
    print("🔗 EXTRACTOR DE URLs FACEBOOK VIA APIFY")
    print("=" * 70)
    print(f"Actor: {ACTOR_POSTS}")
    print(f"Targets: {', '.join(target_handles)}")
    print(f"Rango: {args.since} → {args.before}")
    print(f"Páginas a procesar: {len(page_urls)}")
    print(f"Máx URLs por página: {args.max_urls}")

    # Ejecutar batches
    all_items: list[dict] = []
    total_batches = (len(page_urls) + args.batch_size - 1) // args.batch_size
    for i in range(0, len(page_urls), args.batch_size):
        batch = page_urls[i:i + args.batch_size]
        batch_num = (i // args.batch_size) + 1
        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} página(s))")
        items = run_urls_batch(client, batch, args.max_urls)
        all_items.extend(items)
        print(f"   Acumulado raw items: {len(all_items)}")
        if i + args.batch_size < len(page_urls):
            time.sleep(3)

    # Procesar y filtrar URLs
    rows = []
    seen_urls = set()
    target_set = set(target_handles)

    for item in all_items:
        row = normalize_url_item(item)
        if not row.get("post_url"):
            continue
        if row["post_url"] in seen_urls:
            continue
        if not belongs_to_targets(row, target_set):
            continue
        dt = parse_item_datetime(item)
        if not in_date_range(dt, args.since, args.before):
            continue
        seen_urls.add(row["post_url"])
        rows.append(row)

    rows.sort(key=lambda x: (x.get("fecha_post") or ""), reverse=True)

    # Crear DataFrame
    df_urls = pd.DataFrame(rows, columns=[
        "post_url",
        "page_url",
        "page_handle",
        "fecha_post",
        "fecha_post_date",
    ])

    # Preparar salida
    semana_tag = build_report_tag(args.since, "Facebook")
    output_dir = os.path.join(args.output_dir, semana_tag)
    os.makedirs(output_dir, exist_ok=True)

    # Nombrar archivo con fecha - archivo URLs con patrón semana_urls
    output_csv = os.path.join(output_dir, f"{semana_tag}_urls.csv")

    # Guardar
    df_urls.to_csv(output_csv, index=False, encoding="utf-8")

    print("\n" + "=" * 70)
    print("✅ EXTRACCIÓN COMPLETADA")
    print("=" * 70)
    print(f"URLs descargadas: {len(df_urls)}")
    print(f"Archivo guardado: {output_csv}")
    print("\nEste CSV se puede usar como input para:")
    print("  • 4_extractors_facebook_comentarios.py --input-csv <archivo>")
    print("  • 5_extractors_facebook_posts.py --input-csv <archivo>")


if __name__ == "__main__":
    main()
