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

- `Scripts/orquestador_general.py`
- `Scripts/1_extractors_youtube.py`
- `Scripts/2_extractors_twitter.py`
- `Scripts/3_extractors_medios.py`
- `Scripts/4_extractors_facebook_posts.py`
- `Scripts/5_extractors_facebook_comentarios.py`
- `Scripts/6_consolidador_datos.py`
- `Scripts/7_modelado_temas_claude.py`
- `Scripts/8_influencia_temas.py`
- `Scripts/9_temas_guiados.py`
- `Scripts/10_publicaciones_institucionales_claude.py`

## Variables de entorno

Define las credenciales antes de correr los extractores:

```bash
cp .env.example .env.local
```

Variables requeridas según pipeline:

```bash
YOUTUBE_API_KEY=""
APIFY_TOKEN=""
CLAUDE_API_KEY=""
```

Variables opcionales para YouTube:

```bash
YT_PROXY_HTTP=""
YT_PROXY_HTTPS=""
```

Además, el pipeline de X/Twitter requiere un archivo local `state/x_state.json` con un `storage_state` válido. Ese archivo no va en Git.

## Instalación rápida

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
playwright install chromium
```

`requirements.txt` cubre las librerías usadas por los scripts: `anthropic`, `apify-client`, `cloudscraper`, `google-api-python-client`, `googlenewsdecoder`, `matplotlib`, `numpy`, `pandas`, `playwright`, `python-docx`, `python-dotenv`, `requests`, `scikit-learn`, `trafilatura` y `youtube-transcript-api`.

## Uso recomendado

```bash
python Scripts/orquestador_general.py
```

El detalle script por script de argumentos y prompts quedó en `ORQUESTADOR_ARGUMENTOS.md`.

## Flujo del pipeline

Orden lógico de los pipelines disponibles:

1. `1_extractors_youtube.py`
2. `2_extractors_twitter.py`
3. `3_extractors_medios.py`
4. `4_extractors_facebook_posts.py`
5. `5_extractors_facebook_comentarios.py`
6. `6_consolidador_datos.py`
7. `7_modelado_temas_claude.py`
8. `8_influencia_temas.py`
9. `9_temas_guiados.py`
10. `10_publicaciones_institucionales_claude.py`

Resumen funcional:

- `1`: YouTube. Genera comentarios por búsquedas y transcripciones por canal.
- `2`: Twitter/X. Genera posts institucionales y comentarios públicos.
- `3`: Medios. Genera noticias de medios vía Google News RSS.
- `4`: Facebook posts. Genera posts institucionales de páginas objetivo.
- `5`: Facebook comentarios. Genera comentarios a partir del CSV de posts del pipeline 4.
- `6`: Consolidador. Unifica materiales `.txt` en `Datos/{semana}/material_institucional.txt` y `material_comentarios.txt`.
- `7`: Claude temático general. Analiza el corpus consolidado de `Datos/{semana}/`.
- `8`: Influencia de temas. Trabaja sobre `Datos/{semana}/`.
- `9`: Temas guiados. Trabaja sobre `Datos/{semana}/`.
- `10`: Publicaciones institucionales con Claude. Toma los CSV institucionales de Twitter/X, Facebook y YouTube, arma un solo CSV y genera un análisis comparado entre Gobierno CDMX y Clara Brugada.

## Lógica del orquestador

El orquestador permite dos formas de trabajo:

- `all`: ejecuta todos los pipelines disponibles, del 1 al 10.
- Selección parcial: ejecuta solo los pipelines capturados por el usuario.

También permite dos formas de capturar el contexto temporal:

- Semana ISO: `YYYY-Www`
- Rango explícito: `since` y `before` en formato `YYYY-MM-DD`

Importante:

- Aunque el usuario capture un rango explícito que no corresponda a una semana completa, el resto del pipeline no cambia.
- El etiquetado semanal de carpetas y archivos sigue calculándose con base en la fecha `since`.

Reglas de coordinación y dependencias automáticas:

- Si seleccionas `5` sin `4`, el orquestador inserta `4` automáticamente antes de `5`.
- Si seleccionas `4` y `5` en desorden, el orquestador reordena para ejecutar `4` antes de `5`.
- Si seleccionas `7`, `8` o `9` sin `6`, el orquestador inserta `6` automáticamente antes de esos pipelines.
- Si `6` ya está seleccionado pero aparece después de `7`, `8` o `9`, el orquestador lo reordena para que corra antes.
- Si seleccionas `10` junto con `1`, `2` o `4`, el orquestador mueve `10` al final de esos productores para que consuma material fresco.
- Si seleccionas solo `10`, el orquestador no agrega extractores automáticamente; asume que los CSV institucionales ya existen.

El pipeline `10` no modifica la lógica normal de los extractores. Los extractores siguen produciendo únicamente sus archivos normales; el script 10 consume esos resultados después.

## Ejemplos de selección

Estos ejemplos corresponden al valor que capturas en el prompt `Selecciona pipelines` del orquestador:

- `all`: corre todo el pipeline completo.
- `1,2,4`: corre solo los extractores institucionales de YouTube, Twitter/X y Facebook posts.
- `4,5`: corre posts y luego comentarios de Facebook.
- `5,4`: el orquestador lo corrige y ejecuta `4` antes de `5`.
- `6,7`: consolida y luego corre el análisis temático general con Claude.
- `7`: el orquestador inserta `6` antes.
- `1,2,4,10`: corre extractores institucionales y luego el análisis comparado de publicaciones institucionales.
- `10`: corre solo el análisis de publicaciones institucionales usando CSV ya existentes.

## Notas operativas

- `state/x_state.example.json` es solo una referencia. Debes crear `state/x_state.json` con un `storage_state` válido para correr el extractor de X/Twitter.
- `.env.local` y `state/x_state.json` están ignorados por `.gitignore`; `.env.example` sí se versiona como plantilla.
- Las salidas semanales se generan dentro de `Facebook/`, `Medios/`, `Twitter/`, `Youtube/` y `Claude/`, usando carpetas etiquetadas por semana.
- La carpeta `Influencia_Temas/{semana}/` contiene analisis correlacional de temas sobre polaridad con reportes tecnicos (CSVs) y ejecutivos (KPIs, hallazgos, alertas).
- El pipeline 8 (Analisis de Influencia) requiere que se ejecute primero el pipeline 6 (Consolidador) para generar `material_institucional.txt` e `material_comentarios.txt`.
- La carpeta `Temas_Guiados/{semana}/` contiene clasificacion por tema, top de palabras y reporte textual del analisis guiado.
- El pipeline 9 (Temas Guiados) requiere que se ejecute primero el pipeline 6 (Consolidador), salvo que se indique un `--input-file` explicito.
- El análisis temático con Claude toma su insumo desde `Datos/{semana}/`, donde primero se crea un corpus combinado sin borrar los dos materiales originales.
- El script `10_publicaciones_institucionales_claude.py` consolida en `Datos/{semana}/` un CSV único de publicaciones institucionales de Twitter/X, Facebook y YouTube, y puede generar en `Claude/{semana}/` un análisis comparado entre Gobierno CDMX y Clara Brugada.
  - También genera un CSV de porcentajes por tema y caso, listo para tablas.
- El pipeline 10 consume principalmente:
  - `Twitter/{semana}/{semana}_post_institucionales.csv`
  - `Facebook/{semana}/{semana}_posts.csv`
  - `Youtube/{semana}/{semana}_scripts.csv`
- El pipeline 10 no depende del pipeline 6. Son dos flujos distintos:
  - `6 -> 7/8/9` para análisis sobre materiales `.txt`
  - `1/2/4 -> 10` para análisis comparado de publicaciones institucionales en CSV
- `.gitignore` está configurado para no versionar descargas, cachés ni credenciales futuras.
