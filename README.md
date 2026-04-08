# CDMX_Semanal_Reporte

Repo base para descargar datos semanales de redes y medios sobre el Gobierno de la CDMX, y dejar la salida lista para procesos posteriores de NLP, homologación y análisis.

## Alcance

Este repo parte de `Datos_Radar`, pero quedó limpiado para uso operativo:

- Sin datos históricos descargados.
- Sin la carpeta `Datos_Redes_Sets_Enteros_55_Semanas`.
- Con las carpetas `Facebook`, `Medios`, `Twitter` y `Youtube` vacías, dejando solo la arquitectura.
- Con scripts ajustados para escribir dentro de este mismo repo.
- Sin secretos embebidos en código.

## Estructura

```text
CDMX_Semanal_Reporte/
├── Datos/
├── Facebook/
├── Medios/
├── Scripts/
├── Twitter/
├── Youtube/
└── state/
```

## Scripts incluidos

- `Scripts/00_orquestador_general.py`
- `Scripts/1_extractors_youtube.py`
- `Scripts/2_extractors_twitter.py`
- `Scripts/3_extractors_medios.py`
- `Scripts/4_extractors_facebook_posts.py`
- `Scripts/5_extractors_facebook_comentarios.py`

## Variables de entorno

Define las credenciales antes de correr los extractores:

```bash
export YOUTUBE_API_KEY=""
export APIFY_TOKEN=""
```

Opcionales para YouTube:

```bash
export YT_PROXY_HTTP=""
export YT_PROXY_HTTPS=""
```

## Instalación rápida

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Uso recomendado

```bash
python Scripts/00_orquestador_general.py
```

El detalle script por script de argumentos y prompts quedó en `ORQUESTADOR_ARGUMENTOS.md`.

## Notas operativas

- `state/x_state.example.json` es solo una referencia. Debes crear `state/x_state.json` con un `storage_state` válido para correr el extractor de X/Twitter.
- Las salidas semanales se generan dentro de `Facebook/`, `Medios/`, `Twitter/` y `Youtube/`, usando carpetas como `2026-04-06_Youtube` o `2026-04-06_Facebook`.
- `.gitignore` está configurado para no versionar descargas, cachés ni credenciales futuras.
