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
├── Claude/
├── Datos/
├── Facebook/
├── Influencia_Temas/
├── Medios/
├── Scripts/
├── Temas_Guiados/
├── Twitter/
├── Youtube/
└── state/
```

Donde:

- `Claude/`: Analisis tematicos generados por Claude (corpus combinado + analisis)
- `Datos/`: Archivos consolidados y procesados por semana
- `Influencia_Temas/`: Analisis correlacional de influencia de temas sobre polaridad
- `Temas_Guiados/`: Clasificacion de documentos por temas guiados por palabras clave
- `Facebook/`, `Medios/`, `Twitter/`, `Youtube/`: Descargas por red/fuente

## Scripts incluidos

- `Scripts/00_orquestador_general.py`
- `Scripts/1_extractors_youtube.py`
- `Scripts/2_extractors_twitter.py`
- `Scripts/3_extractors_medios.py`
- `Scripts/4_extractors_facebook_posts.py`
- `Scripts/5_extractors_facebook_comentarios.py`
- `Scripts/6_consolidador_datos.py`
- `Scripts/7_modelado_temas_claude.py`
- `Scripts/8_influencia_temas.py`
- `Scripts/9_temas_guiados.py`

## Variables de entorno

Define las credenciales antes de correr los extractores:

```bash
export YOUTUBE_API_KEY=""
export APIFY_TOKEN=""
export CLAUDE_API_KEY=""
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
- Las salidas semanales se generan dentro de `Facebook/`, `Medios/`, `Twitter/`, `Youtube/` y `Claude/`, usando carpetas etiquetadas por semana.
- La carpeta `Influencia_Temas/{semana}/` contiene analisis correlacional de temas sobre polaridad con reportes tecnicos (CSVs) y ejecutivos (KPIs, hallazgos, alertas).
- El pipeline 8 (Analisis de Influencia) requiere que se ejecute primero el pipeline 6 (Consolidador) para generar `material_institucional.txt` e `material_comentarios.txt`.
- La carpeta `Temas_Guiados/{semana}/` contiene clasificacion por tema, top de palabras y reporte textual del analisis guiado.
- El pipeline 9 (Temas Guiados) requiere que se ejecute primero el pipeline 6 (Consolidador), salvo que se indique un `--input-file` explicito.
- El análisis temático con Claude toma su insumo desde `Datos/{semana}/`, donde primero se crea un corpus combinado sin borrar los dos materiales originales.
- `.gitignore` está configurado para no versionar descargas, cachés ni credenciales futuras.
